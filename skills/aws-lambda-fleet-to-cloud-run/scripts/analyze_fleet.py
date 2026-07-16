#!/usr/bin/env python3
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
analyze_fleet.py — Fleet-level Lambda discovery and dependency graph builder.

Recursively walks a monorepo root to discover all AWS Lambda functions across
SAM, Serverless Framework, and Terraform IaC files. Builds a fleet manifest
with a dependency graph (dependency_edges) for migration wave sequencing.

Companion to the aws-lambda-fleet-to-cloud-run skill. For per-function deep
analysis, use analyze_lambda.py from the aws-lambda-to-cloud-run-migration skill.

Usage:
    python scripts/analyze_fleet.py <repo_root> [--output <dir>] [--summary]
"""

import os
import re
import sys
import json
import argparse
from collections import defaultdict

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


# ---------------------------------------------------------------------------
# Patterns for detecting inter-Lambda invocations in source code
# ---------------------------------------------------------------------------

# Direct boto3 Lambda invocations: boto3.client('lambda').invoke(FunctionName=...)
DIRECT_INVOKE_PATTERN = re.compile(
    r"""boto3\.client\s*\(\s*['"]lambda['"]\s*\).*?invoke\s*\(.*?FunctionName\s*=\s*['"]([^'"]+)['"]""",
    re.DOTALL
)

# AWS SDK v3 Node.js Lambda invocations: new LambdaClient(...).send(new InvokeCommand({FunctionName: ...}))
NODE_INVOKE_PATTERN = re.compile(
    r"""InvokeCommand\s*\(\s*\{[^}]*FunctionName\s*:\s*['"]([^'"]+)['"]""",
    re.DOTALL
)

# SNS publish calls — capture topic ARN or name
SNS_PUBLISH_PYTHON = re.compile(
    r"""sns\.publish\s*\([^)]*TopicArn\s*=\s*['"]([^'"]+)['"]""",
    re.DOTALL
)
SNS_PUBLISH_NODE = re.compile(
    r"""PublishCommand\s*\(\s*\{[^}]*TopicArn\s*:\s*['"`]([^'"`]+)['"`]""",
    re.DOTALL
)

# SQS send_message — capture queue URL or name
SQS_SEND_PYTHON = re.compile(
    r"""sqs\.send_message\s*\([^)]*QueueUrl\s*=\s*['"]([^'"]+)['"]""",
    re.DOTALL
)
SQS_SEND_NODE = re.compile(
    r"""SendMessageCommand\s*\(\s*\{[^}]*QueueUrl\s*:\s*['"`]([^'"`]+)['"`]""",
    re.DOTALL
)

# S3 write (bucket name from put_object)
S3_WRITE_PYTHON = re.compile(
    r"""s3\.put_object\s*\([^)]*Bucket\s*=\s*['"]([^'"]+)['"]""",
    re.DOTALL
)

# Step Functions state machine ARN references
SFNO_PATTERN = re.compile(r"""stepfunctions.*start_execution.*StateMachineArn\s*=\s*['"]([^'"]+)['"]""", re.DOTALL)


# ---------------------------------------------------------------------------
# Complexity rating
# ---------------------------------------------------------------------------

def rate_complexity(func_info: dict) -> str:
    """Rate migration complexity based on function attributes."""
    triggers = func_info.get("triggers", [])
    invokes = func_info.get("invokes", [])
    shared = func_info.get("shared_resources", [])
    has_vpc = bool(func_info.get("vpc"))
    has_layers = bool(func_info.get("layers"))
    memory = func_info.get("memory_mb", 0)

    score = 0
    # Direct invocations or step functions = high complexity
    if any(r.get("via") == "direct_invoke" for r in invokes):
        score += 3
    if any(r.get("via") == "step_function" for r in invokes):
        score += 3
    # VPC and layers add medium complexity
    if has_vpc:
        score += 2
    if has_layers:
        score += 1
    # High memory often means heavy processing
    if memory >= 1024:
        score += 1
    # SNS/SQS consumers are medium
    if any(t.lower() in ("sns", "sqs") for t in triggers):
        score += 1

    if score >= 4:
        return "High"
    elif score >= 2:
        return "Medium"
    return "Low"


# ---------------------------------------------------------------------------
# IaC parsers
# ---------------------------------------------------------------------------

# SAM/SLS regex patterns (used when PyYAML is unavailable)
_SAM_FUNCTION_RE = re.compile(r'^\s{2}(\w[\w-]*):\s*$', re.MULTILINE)
_SAM_TYPE_RE = re.compile(r'Type:\s*AWS::Serverless::Function')
_SAM_RUNTIME_RE = re.compile(r'Runtime:\s*(\S+)')
_SAM_HANDLER_RE = re.compile(r'Handler:\s*(\S+)')
_SAM_MEMORY_RE = re.compile(r'MemorySize:\s*(\d+)')
_SAM_TIMEOUT_RE = re.compile(r'Timeout:\s*(\d+)')
_SAM_TRIGGER_TYPE_RE = re.compile(r'Type:\s*(Api|HttpApi|SNS|SQS|S3|Schedule|DynamoDB|Kinesis|Kafka|MSK|CloudWatchLogs|Cognito|IoTRule|AlexaSkill|EventBridgeRule)')
_SAM_VPC_RE = re.compile(r'VpcConfig:')
_SAM_LAYERS_RE = re.compile(r'Layers:')
_SAM_GLOBAL_RUNTIME_RE = re.compile(r'^Globals:.*?Runtime:\s*(\S+)', re.DOTALL | re.MULTILINE)


def _parse_sam_regex(file_path: str, content: str) -> list:
    """Regex-based SAM parser fallback (no PyYAML required)."""
    functions = []
    global_runtime_m = _SAM_GLOBAL_RUNTIME_RE.search(content)
    global_runtime = global_runtime_m.group(1) if global_runtime_m else "unknown"

    # Find all top-level resource blocks by splitting on 2-space-indented keys
    # We look for blocks that contain 'AWS::Serverless::Function'
    # Split content into resource-like chunks at 2-space keys
    lines = content.splitlines()
    blocks = {}  # resource_name -> block_content
    current_name = None
    current_lines = []
    in_resources = False

    for line in lines:
        if re.match(r'^Resources:', line):
            in_resources = True
            continue
        if in_resources and re.match(r'^[A-Za-z]', line) and not line.startswith(' '):
            # New top-level section ends Resources
            if current_name:
                blocks[current_name] = '\n'.join(current_lines)
            in_resources = False
            current_name = None
            current_lines = []
            continue
        if in_resources:
            m = re.match(r'^  (\w[\w-]*):\s*$', line)
            if m:
                if current_name:
                    blocks[current_name] = '\n'.join(current_lines)
                current_name = m.group(1)
                current_lines = [line]
            elif current_name:
                current_lines.append(line)
    if current_name and current_lines:
        blocks[current_name] = '\n'.join(current_lines)

    for res_name, block in blocks.items():
        if not _SAM_TYPE_RE.search(block):
            continue
        runtime_m = _SAM_RUNTIME_RE.search(block)
        runtime = runtime_m.group(1) if runtime_m else global_runtime
        handler_m = _SAM_HANDLER_RE.search(block)
        handler = handler_m.group(1) if handler_m else "unknown"
        memory_m = _SAM_MEMORY_RE.search(block)
        memory = int(memory_m.group(1)) if memory_m else 128
        timeout_m = _SAM_TIMEOUT_RE.search(block)
        timeout = int(timeout_m.group(1)) if timeout_m else 3
        triggers = [m.group(1) for m in _SAM_TRIGGER_TYPE_RE.finditer(block)]
        functions.append({
            "name": res_name,
            "runtime": runtime,
            "handler": handler,
            "memory_mb": memory,
            "timeout_s": timeout,
            "triggers": triggers,
            "layers": bool(_SAM_LAYERS_RE.search(block)),
            "vpc": bool(_SAM_VPC_RE.search(block)),
            "iam_role": None,
            "env_var_keys": [],
            "iac_file": file_path,
            "iac_type": "AWS SAM",
        })
    return functions


def parse_sam(file_path: str) -> list:
    """Extract Lambda function definitions from a SAM/CloudFormation template."""
    functions = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if HAS_YAML:
            data = yaml.safe_load(content) or {}
            if "Resources" not in data:
                return functions
            for res_name, res_data in data.get("Resources", {}).items():
                if not isinstance(res_data, dict):
                    continue
                if res_data.get("Type") != "AWS::Serverless::Function":
                    continue
                props = res_data.get("Properties", {})
                global_runtime = data.get("Globals", {}).get("Function", {}).get("Runtime", "unknown")
                triggers = []
                for ev_name, ev_data in props.get("Events", {}).items():
                    if isinstance(ev_data, dict):
                        triggers.append(ev_data.get("Type", "Unknown"))
                functions.append({
                    "name": res_name,
                    "runtime": props.get("Runtime", global_runtime),
                    "handler": props.get("Handler", "unknown"),
                    "memory_mb": props.get("MemorySize", 128),
                    "timeout_s": props.get("Timeout", 3),
                    "triggers": triggers,
                    "layers": props.get("Layers", []),
                    "vpc": bool(props.get("VpcConfig")),
                    "iam_role": props.get("Role"),
                    "env_var_keys": list(props.get("Environment", {}).get("Variables", {}).keys()),
                    "iac_file": file_path,
                    "iac_type": "AWS SAM",
                })
        else:
            # Regex fallback — no PyYAML
            functions = _parse_sam_regex(file_path, content)
    except Exception as e:
        print(f"  [WARN] Could not parse SAM file {file_path}: {e}", file=sys.stderr)
    return functions


_SLS_PROVIDER_AWS_RE = re.compile(r'^\s*name:\s*aws\s*$', re.MULTILINE)
_SLS_PROVIDER_RUNTIME_RE = re.compile(r'^provider:[\s\S]*?runtime:\s*(\S+)', re.MULTILINE)
_SLS_FUNC_BLOCK_RE = re.compile(r'^functions:[\s\S]*', re.MULTILINE)
_SLS_FUNC_NAME_RE = re.compile(r'^  (\w[\w-]*):\s*$', re.MULTILINE)
_SLS_HANDLER_RE = re.compile(r'handler:\s*(\S+)')
_SLS_RUNTIME_RE = re.compile(r'runtime:\s*(\S+)')
_SLS_MEMORY_RE = re.compile(r'memorySize:\s*(\d+)')
_SLS_TIMEOUT_RE = re.compile(r'timeout:\s*(\d+)')
_SLS_EVENT_KEY_RE = re.compile(r'^\s{6}-(\w+):', re.MULTILINE)
_SLS_VPC_RE = re.compile(r'vpc:')
_SLS_LAYERS_RE = re.compile(r'layers:')


def _parse_sls_regex(file_path: str, content: str) -> list:
    """Regex-based Serverless Framework parser fallback."""
    functions = []
    if not _SLS_PROVIDER_AWS_RE.search(content):
        return functions
    runtime_m = _SLS_PROVIDER_RUNTIME_RE.search(content)
    global_runtime = runtime_m.group(1) if runtime_m else "unknown"

    # Isolate functions: block
    func_block_m = _SLS_FUNC_BLOCK_RE.search(content)
    if not func_block_m:
        return functions
    func_block = func_block_m.group(0)

    lines = func_block.splitlines()
    blocks = {}
    current_name = None
    current_lines = []
    in_functions = False

    for line in lines:
        if re.match(r'^functions:', line):
            in_functions = True
            continue
        if in_functions and re.match(r'^[A-Za-z]', line) and not line.startswith(' '):
            if current_name:
                blocks[current_name] = '\n'.join(current_lines)
            in_functions = False
            break
        if in_functions:
            m = re.match(r'^  (\w[\w-]*):\s*$', line)
            if m:
                if current_name:
                    blocks[current_name] = '\n'.join(current_lines)
                current_name = m.group(1)
                current_lines = [line]
            elif current_name:
                current_lines.append(line)
    if current_name and current_lines:
        blocks[current_name] = '\n'.join(current_lines)

    for func_name, block in blocks.items():
        handler_m = _SLS_HANDLER_RE.search(block)
        runtime_m = _SLS_RUNTIME_RE.search(block)
        memory_m = _SLS_MEMORY_RE.search(block)
        timeout_m = _SLS_TIMEOUT_RE.search(block)
        triggers = [m.group(1) for m in _SLS_EVENT_KEY_RE.finditer(block)]
        functions.append({
            "name": func_name,
            "runtime": runtime_m.group(1) if runtime_m else global_runtime,
            "handler": handler_m.group(1) if handler_m else "unknown",
            "memory_mb": int(memory_m.group(1)) if memory_m else 128,
            "timeout_s": int(timeout_m.group(1)) if timeout_m else 6,
            "triggers": triggers,
            "layers": bool(_SLS_LAYERS_RE.search(block)),
            "vpc": bool(_SLS_VPC_RE.search(block)),
            "iam_role": None,
            "env_var_keys": [],
            "iac_file": file_path,
            "iac_type": "Serverless Framework",
        })
    return functions


def parse_serverless_framework(file_path: str) -> list:
    """Extract Lambda function definitions from a Serverless Framework config."""
    functions = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if HAS_YAML:
            data = yaml.safe_load(content) or {}
            if data.get("provider", {}).get("name") != "aws":
                return functions
            provider_runtime = data.get("provider", {}).get("runtime", "unknown")
            for func_name, func_data in data.get("functions", {}).items():
                if not isinstance(func_data, dict):
                    continue
                triggers = []
                for event in func_data.get("events", []):
                    if isinstance(event, dict):
                        triggers.append(list(event.keys())[0])
                functions.append({
                    "name": func_name,
                    "runtime": func_data.get("runtime", provider_runtime),
                    "handler": func_data.get("handler", "unknown"),
                    "memory_mb": func_data.get("memorySize", 128),
                    "timeout_s": func_data.get("timeout", 6),
                    "triggers": triggers,
                    "layers": func_data.get("layers", []),
                    "vpc": bool(func_data.get("vpc")),
                    "iam_role": None,
                    "env_var_keys": list(func_data.get("environment", {}).keys()),
                    "iac_file": file_path,
                    "iac_type": "Serverless Framework",
                })
        else:
            functions = _parse_sls_regex(file_path, content)
    except Exception as e:
        print(f"  [WARN] Could not parse Serverless Framework file {file_path}: {e}", file=sys.stderr)
    return functions


def parse_terraform(root_dir: str) -> list:
    """Extract aws_lambda_function resources from Terraform .tf files."""
    functions = []
    for dirpath, _, files in os.walk(root_dir):
        for file in files:
            if not file.endswith(".tf"):
                continue
            path = os.path.join(dirpath, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Only process AWS provider files
                is_aws = bool(
                    re.search(r"provider\s+[\"']aws[\"']", content) or
                    re.search(r"source\s*=\s*[\"']hashicorp/aws[\"']", content)
                )
                if not is_aws:
                    continue

                for m in re.finditer(
                    r'resource\s+["\']aws_lambda_function["\']\s+["\'](?P<name>[\w-]+)["\']',
                    content
                ):
                    block_start = m.start()
                    # Grab ~800 chars of block for attribute extraction
                    snippet = content[block_start:block_start + 800]
                    runtime_m = re.search(r'runtime\s*=\s*["\']([^"\']+)["\']', snippet)
                    memory_m = re.search(r'memory_size\s*=\s*(\d+)', snippet)
                    timeout_m = re.search(r'timeout\s*=\s*(\d+)', snippet)
                    vpc_m = re.search(r'vpc_config\s*\{', snippet)
                    functions.append({
                        "name": m.group("name"),
                        "runtime": runtime_m.group(1) if runtime_m else "unknown",
                        "handler": "unknown",
                        "memory_mb": int(memory_m.group(1)) if memory_m else 128,
                        "timeout_s": int(timeout_m.group(1)) if timeout_m else 3,
                        "triggers": [],  # Terraform triggers are in separate resources
                        "layers": [],
                        "vpc": bool(vpc_m),
                        "iam_role": None,
                        "env_var_keys": [],
                        "iac_file": path,
                        "iac_type": "AWS Terraform",
                    })
            except Exception as e:
                print(f"  [WARN] Could not parse Terraform file {path}: {e}", file=sys.stderr)
    return functions


# ---------------------------------------------------------------------------
# Source code dependency scanner
# ---------------------------------------------------------------------------

def scan_source_for_dependencies(func_name: str, func_dir: str) -> list:
    """
    Scan source files in func_dir for inter-Lambda invocations, shared SNS/SQS
    topics, and S3 writes. Returns a list of dependency edge dicts.
    """
    edges = []
    if not os.path.isdir(func_dir):
        return edges

    source_extensions = (".py", ".js", ".ts", ".go", ".java", ".cs", ".php")
    for dirpath, _, files in os.walk(func_dir):
        # Skip dependency directories
        skip_dirs = {"node_modules", ".venv", "__pycache__", "vendor", "dist", "build"}
        dirpath_parts = set(dirpath.split(os.sep))
        if skip_dirs & dirpath_parts:
            continue

        for file in files:
            if not any(file.endswith(ext) for ext in source_extensions):
                continue
            path = os.path.join(dirpath, file)
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
            except Exception:
                continue

            # Direct invocations (Python boto3)
            for m in DIRECT_INVOKE_PATTERN.finditer(content):
                target = m.group(1)
                if target != func_name:
                    edges.append({"from": func_name, "to": target, "via": "direct_invoke", "resource": None})

            # Direct invocations (Node.js SDK v3)
            for m in NODE_INVOKE_PATTERN.finditer(content):
                target = m.group(1)
                if target != func_name:
                    edges.append({"from": func_name, "to": target, "via": "direct_invoke", "resource": None})

            # SNS publish (Python)
            for m in SNS_PUBLISH_PYTHON.finditer(content):
                resource = m.group(1).split(":")[-1]  # extract topic name from ARN
                edges.append({"from": func_name, "to": None, "via": "sns_topic", "resource": resource})

            # SNS publish (Node.js)
            for m in SNS_PUBLISH_NODE.finditer(content):
                resource = m.group(1).split(":")[-1]
                edges.append({"from": func_name, "to": None, "via": "sns_topic", "resource": resource})

            # SQS send (Python)
            for m in SQS_SEND_PYTHON.finditer(content):
                resource = m.group(1).rstrip("/").split("/")[-1]  # extract queue name from URL
                edges.append({"from": func_name, "to": None, "via": "sqs_queue", "resource": resource})

            # SQS send (Node.js)
            for m in SQS_SEND_NODE.finditer(content):
                resource = m.group(1).rstrip("/").split("/")[-1]
                edges.append({"from": func_name, "to": None, "via": "sqs_queue", "resource": resource})

            # S3 write
            for m in S3_WRITE_PYTHON.finditer(content):
                resource = m.group(1)
                edges.append({"from": func_name, "to": None, "via": "s3_write", "resource": resource})

            # Step Functions
            for m in SFNO_PATTERN.finditer(content):
                resource = m.group(1)
                edges.append({"from": func_name, "to": None, "via": "step_function", "resource": resource})

    # Deduplicate edges
    seen = set()
    unique_edges = []
    for e in edges:
        key = (e["from"], e["to"], e["via"], e["resource"])
        if key not in seen:
            seen.add(key)
            unique_edges.append(e)
    return unique_edges


# ---------------------------------------------------------------------------
# Shared resource cross-referencing (SNS/SQS: link producer → consumer)
# ---------------------------------------------------------------------------

def link_shared_resources(functions: list, all_edges: list) -> list:
    """
    Post-process edges: for SNS topics and SQS queues, link producers to
    consumers by matching trigger types against resource names.
    """
    # Build map: resource_name → list of consuming function names (from triggers)
    consumers = defaultdict(list)
    for func in functions:
        for trigger in func.get("triggers", []):
            # SAM/SLS trigger types: "SNS", "SQS", "sns", "sqs"
            if trigger.lower() in ("sns", "sqs"):
                # We can't resolve the exact resource at IaC parse time without
                # reading event trigger config deeply; mark as potential consumer
                consumers[func.get("iac_type", "") + "/" + func["name"]].append(func["name"])

    # For shared-resource edges, try to resolve the consumer from IaC if available
    enriched = []
    for edge in all_edges:
        if edge["via"] in ("sns_topic", "sqs_queue") and edge["to"] is None:
            # Look for functions that have a matching trigger with that resource name
            matched_consumers = [
                f["name"] for f in functions
                if any(
                    edge["resource"] and edge["resource"].lower() in str(t).lower()
                    for t in f.get("triggers", [])
                )
                and f["name"] != edge["from"]
            ]
            if matched_consumers:
                for consumer in matched_consumers:
                    enriched.append({**edge, "to": consumer})
                continue
        enriched.append(edge)
    return enriched


# ---------------------------------------------------------------------------
# Summary printer
# ---------------------------------------------------------------------------

def print_summary(manifest: dict):
    summary = manifest["fleet_summary"]
    functions = manifest["functions"]
    edges = manifest["dependency_edges"]

    print(f"\n{'='*70}")
    print(f"  Lambda Fleet Migration Summary")
    print(f"  Repo: {manifest['metadata']['source_directory']}")
    print(f"{'='*70}\n")
    print(f"  Total functions : {summary['total_functions']}")
    print(f"  IaC types       : {', '.join(f'{k} ({v})' for k, v in summary['iac_types'].items())}")
    print(f"  Runtimes        : {', '.join(f'{k} ({v})' for k, v in summary['runtimes'].items())}")
    print(f"  Trigger types   : {', '.join(f'{k} ({v})' for k, v in summary['trigger_types'].items())}")
    print(f"  Dependency edges: {len(edges)}")

    print(f"\n  {'Function':<30} {'Runtime':<15} {'Triggers':<20} {'Complexity':<12} {'VPC'}")
    print(f"  {'-'*30} {'-'*15} {'-'*20} {'-'*12} {'-'*5}")
    for fn in functions:
        triggers_str = ", ".join(fn.get("triggers", [])) or "none"
        vpc_str = "yes" if fn.get("vpc") else "no"
        print(f"  {fn['name']:<30} {fn['runtime']:<15} {triggers_str:<20} {fn['complexity']:<12} {vpc_str}")

    if edges:
        print(f"\n  Dependency Edges:")
        for e in edges:
            target = e['to'] or f"[{e['resource']}]"
            print(f"    {e['from']} → {target}  (via {e['via']})")

    print(f"\n{'='*70}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(root_dir: str, output_dir: str = None, print_human_summary: bool = False):
    root_dir = os.path.abspath(root_dir)
    output_dir = output_dir or os.getcwd()
    print(f"Scanning fleet in: {root_dir}")

    # --- Phase 1: discover IaC files ---
    all_functions = []
    iac_files_found = []

    skip_dirs = {"node_modules", ".venv", "__pycache__", "cdk.out", ".git", "vendor"}

    for dirpath, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for file in files:
            path = os.path.join(dirpath, file)
            if file in ("template.yaml", "template.yml"):
                discovered = parse_sam(path)
                if discovered:
                    all_functions.extend(discovered)
                    iac_files_found.append(path)
                    print(f"  [SAM] Found {len(discovered)} function(s) in {path}")
            elif file in ("serverless.yml", "serverless.yaml"):
                discovered = parse_serverless_framework(path)
                if discovered:
                    all_functions.extend(discovered)
                    iac_files_found.append(path)
                    print(f"  [SLS] Found {len(discovered)} function(s) in {path}")

    # Terraform: scan entire tree once
    tf_functions = parse_terraform(root_dir)
    if tf_functions:
        all_functions.extend(tf_functions)
        print(f"  [TF]  Found {len(tf_functions)} Lambda resource(s) in Terraform files")

    if not all_functions:
        print("\n⚠️  No Lambda functions discovered. Check that the repo root contains "
              "SAM template.yaml, serverless.yml, or Terraform .tf files.", file=sys.stderr)
        sys.exit(1)

    # Deduplicate by name (a function may appear in both a SAM file and Terraform)
    seen_names = set()
    unique_functions = []
    for fn in all_functions:
        if fn["name"] not in seen_names:
            seen_names.add(fn["name"])
            unique_functions.append(fn)
    all_functions = unique_functions

    print(f"\n  Total unique functions discovered: {len(all_functions)}")

    # --- Phase 2: source code scanning for dependencies ---
    all_edges = []
    for fn in all_functions:
        iac_dir = os.path.dirname(fn["iac_file"])
        fn_dir = None

        # Priority 1: derive source dir from the handler path
        # e.g. "functions/create_order/handler.handler" -> "<iac_dir>/functions/create_order/"
        handler = fn.get("handler", "unknown")
        if handler and handler not in ("unknown", "") and "/" in handler:
            handler_rel_dir = os.path.dirname(handler)
            handler_abs_dir = os.path.join(iac_dir, handler_rel_dir)
            if os.path.isdir(handler_abs_dir):
                fn_dir = handler_abs_dir

        # Priority 2: look for a subdirectory named after the function
        if fn_dir is None:
            for name_variant in [
                fn["name"].lower().replace("-", "_"),
                fn["name"].lower(),
                fn["name"],
            ]:
                candidate = os.path.join(iac_dir, name_variant)
                if os.path.isdir(candidate):
                    fn_dir = candidate
                    break

        # Priority 3: fall back to the IaC root (broader scan)
        if fn_dir is None:
            fn_dir = iac_dir

        edges = scan_source_for_dependencies(fn["name"], fn_dir)
        fn["invokes"] = [e for e in edges if e["via"] == "direct_invoke"]
        fn["shared_resources"] = [e for e in edges if e["via"] != "direct_invoke"]
        all_edges.extend(edges)

    # Cross-reference shared resources
    all_edges = link_shared_resources(all_functions, all_edges)

    # Rate complexity
    for fn in all_functions:
        fn["complexity"] = rate_complexity(fn)

    # --- Phase 3: build manifest ---
    runtimes = defaultdict(int)
    trigger_types = defaultdict(int)
    iac_types = defaultdict(int)
    for fn in all_functions:
        runtimes[fn["runtime"]] += 1
        iac_types[fn["iac_type"]] += 1
        for t in fn.get("triggers", []):
            trigger_types[t] += 1

    manifest = {
        "metadata": {
            "source_directory": root_dir,
            "description": "AWS Lambda Fleet Migration Manifest — aws-lambda-fleet-to-cloud-run skill",
            "skill_version": "1.0.0",
        },
        "fleet_summary": {
            "total_functions": len(all_functions),
            "runtimes": dict(runtimes),
            "trigger_types": dict(trigger_types),
            "iac_types": dict(iac_types),
            "total_dependency_edges": len(all_edges),
        },
        "functions": all_functions,
        "dependency_edges": all_edges,
    }

    manifest_path = os.path.join(output_dir, "fleet_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\n✅ Fleet analysis complete. Manifest written to: {manifest_path}")
    print("Agent Instruction: Read 'fleet_manifest.json' immediately. "
          "Use fleet_summary for the overall picture; functions[] for per-function details; "
          "dependency_edges[] for the dependency graph used in wave sequencing.")

    if print_human_summary:
        print_summary(manifest)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze an AWS Lambda monorepo for fleet-level Cloud Run migration planning."
    )
    parser.add_argument("directory", help="Path to the monorepo root directory to scan.")
    parser.add_argument(
        "--output", default=None,
        help="Directory where fleet_manifest.json will be written. Defaults to cwd."
    )
    parser.add_argument(
        "--summary", action="store_true", default=False,
        help="Print a human-readable fleet summary table to stdout after analysis."
    )
    args = parser.parse_args()
    main(args.directory, output_dir=args.output, print_human_summary=args.summary)
