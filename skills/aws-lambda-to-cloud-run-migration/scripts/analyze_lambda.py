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

import os
import re
import sys
import json
import ast
import argparse

# Attempt to import PyYAML for IaC parsing, fallback to Regex if unavailable
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# Common AWS Lock-in patterns for non-Python languages
REGEX_PATTERNS = {
    "SDK (Node.js)": r"require\s*\(\s*['\"]aws-sdk['\"]\s*\)|import.*from\s*['\"]@aws-sdk",
    "SDK (PHP)": r"Aws\\Sdk|new\s+Aws\\",
    "SDK (Java)": r"import\s+com\.amazonaws|import\s+software\.amazon\.awssdk",
    "SDK (Go)": r"\"github\.com/aws/aws-sdk-go",
    "SDK (.NET/C#)": r"using\s+Amazon\.Lambda|using\s+AWSSDK|using\s+Amazon\.DynamoDBv2|using\s+Amazon\.S3|using\s+Amazon\.SQS|using\s+Amazon\.SimpleNotificationService|using\s+Amazon\.SecretsManager",
    "Lambda Handler (.NET)": r"ILambdaContext|FunctionHandler|LambdaEntryPoint|Amazon\.Lambda\.AspNetCoreServer|Amazon\.Lambda\.APIGatewayEvents",
    "Lambda Powertools (.NET)": r"AWS\.Lambda\.Powertools|\[Logging\]|\[Tracing\]|\[Metrics\]",
    "Bref Framework": r"Bref\\Context|bref/bref",
    "Bref Handler (PHP)": r"return\s+function\s*\(\s*\$event",
    "Laravel Framework": r"Illuminate\\\\|Laravel\\\\",
    "Symfony Framework": r"Symfony\\\\Component",
    "PHP Database (PDO/Eloquent)": r"new\s+PDO\(|DB::table\(|Eloquent",
    "Raw HTTP (Node.js)": r"axios\.(get|post|put|delete|request)\(|fetch\(|https?\.request\(",
    "Raw HTTP (PHP)": r"GuzzleHttp\\Client|curl_init|file_get_contents\(",
    "Raw HTTP (Java)": r"HttpClient\.newHttpClient|HttpURLConnection",
    "Raw HTTP (Go)": r"http\.(Get|Post|Do)",
    "Potential Secrets/IDs": r"(?i)(client_id|client_secret|client-id|client-secret|api_key|api-key|secret_key|secret-key|access_key|access-key)\s*[:=]\s*['\"][a-zA-Z0-9_\-]{8,}['\"]",
    "Hardcoded AWS Credentials": r"(?i)(aws_access_key_id|aws_secret_access_key)\s*[:=]\s*['\"][a-zA-Z0-9_\-]{16,}['\"]",
    "Messaging (SNS/SQS)": r"sns\.publish|sns\.subscribe|sqs\.send_message|sqs\.receive_message|PublishRequest|SendMessageRequest",
    "Database (DynamoDB)": r"dynamodb\.put_item|dynamodb\.get_item|Table\(['\"]|DynamoDbClient",
    "Storage (S3)": r"s3\.put_object|s3\.get_object|PutObjectRequest|GetObjectRequest",
    "Lambda Handler": r"exports\.handler\s*=|function\s+.*\(.*\$event|implements\s+RequestHandler|lambda\.Start\(",
    "Database Connection Pools": r"(?i)(createPool|new\s+Pool|mongoose\.connect|MongoClient|mysql\.createConnection)"
}

# AWS CDK detection patterns (TypeScript / Python)
CDK_PATTERNS = {
    "CDK Stack (TypeScript)": r"extends\s+Stack|new\s+\w+Stack\(|import.*from\s*['\"]aws-cdk-lib['\"]|import.*from\s*['\"]@aws-cdk",
    "CDK Stack (Python)": r"from\s+aws_cdk\s+import|import\s+aws_cdk|Stack\.__init__",
    "Lambda Construct (CDK)": r"new\s+lambda\.Function\(|new\s+NodejsFunction\(|aws_lambda\.Function\(",
    "API Gateway Construct": r"new\s+apigw\.|new\s+apigateway\.|aws_apigateway\.LambdaRestApi",
    "SNS/SQS Construct": r"new\s+sns\.|new\s+sqs\.|aws_sns\.|aws_sqs\.",
    "DynamoDB Construct": r"new\s+dynamodb\.|aws_dynamodb\.Table\(",
    "S3 Construct": r"new\s+s3\.Bucket\(|aws_s3\.Bucket\(",
    "EventBridge Construct": r"new\s+events\.|aws_events\.Rule\(",
}

class PythonLambdaVisitor(ast.NodeVisitor):
    def __init__(self):
        self.findings = {
            "sdk_imports": [],
            "handlers": [],
            "global_db_connections": [],
            "raw_http": [],
            "aws_service_calls": []
        }
        self.in_function = False

    def visit_Import(self, node):
        for alias in node.names:
            if 'boto3' in alias.name or 'botocore' in alias.name:
                self.findings["sdk_imports"].append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module and ('boto3' in node.module or 'botocore' in node.module):
            self.findings["sdk_imports"].append(node.module)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        if 'handler' in node.name.lower():
            self.findings["handlers"].append(node.name)
        
        old_in_function = self.in_function
        self.in_function = True
        self.generic_visit(node)
        self.in_function = old_in_function

    def _get_call_name(self, node):
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                return f"{node.func.value.id}.{node.func.attr}"
            return f"*.{node.func.attr}"
        return "unknown"

    def visit_Assign(self, node):
        # Look for global connections (outside function definitions)
        if not self.in_function:
            if isinstance(node.value, ast.Call):
                call_name = self._get_call_name(node.value).lower()
                db_keywords = ['connect', 'create_engine', 'pool', 'psycopg2', 'pymysql', 'sqlalchemy', 'mongo']
                if any(kw in call_name for kw in db_keywords):
                    self.findings["global_db_connections"].append(call_name)
        self.generic_visit(node)
        
    def visit_Call(self, node):
        call_name = self._get_call_name(node).lower()
        if 'requests.' in call_name:
            self.findings["raw_http"].append(call_name)
        
        aws_keywords = ['boto3.client', 'put_object', 'get_object', 'publish', 'send_message', 'put_item']
        if any(kw in call_name for kw in aws_keywords):
            self.findings["aws_service_calls"].append(call_name)
            
        self.generic_visit(node)

def analyze_python_ast(file_path):
    findings = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=file_path)
        visitor = PythonLambdaVisitor()
        visitor.visit(tree)
        
        # Clean empty lists
        for k, v in visitor.findings.items():
            if v:
                findings[k] = list(set(v)) # deduplicate
    except SyntaxError:
        findings["error"] = "Syntax error parsing Python file"
    except Exception as e:
        findings["error"] = str(e)
    return findings

def analyze_generic_regex(file_path):
    findings = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            for label, pattern in REGEX_PATTERNS.items():
                matches = re.findall(pattern, content)
                if matches:
                    findings[label] = len(matches)
    except Exception:
        pass 
    return findings

def analyze_composer_json(file_path):
    findings = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            require = data.get('require', {})
            require_dev = data.get('require-dev', {})
            all_deps = {**require, **require_dev}
            
            if 'aws/aws-sdk-php' in all_deps:
                findings['aws_sdk'] = all_deps['aws/aws-sdk-php']
            
            if 'bref/bref' in all_deps:
                findings['bref_framework'] = all_deps['bref/bref']
                
            if 'laravel/framework' in all_deps:
                findings['laravel_framework'] = all_deps['laravel/framework']
            elif 'symfony/framework-bundle' in all_deps:
                findings['symfony_framework'] = all_deps['symfony/framework-bundle']
            elif 'slim/slim' in all_deps:
                findings['slim_framework'] = all_deps['slim/slim']
                
            gcp_deps = {k: v for k, v in all_deps.items() if k.startswith('google/cloud-')}
            if gcp_deps:
                findings['gcp_sdks_present'] = gcp_deps
                
            if 'php' in require:
                findings['php_version'] = require['php']
                
    except Exception as e:
        findings["error"] = f"Failed to parse composer.json: {e}"
    return findings


# AWS package names that signal lock-in for Node.js projects
_NODE_AWS_PACKAGES = {
    'aws-sdk': 'AWS SDK v2 (monolithic)',
    'amazon-dax-client': 'DynamoDB Accelerator (DAX) client',
    'aws-lambda': 'Lambda local emulator',
    '@aws-sdk/client-s3': 'AWS SDK v3 — S3',
    '@aws-sdk/client-sns': 'AWS SDK v3 — SNS',
    '@aws-sdk/client-sqs': 'AWS SDK v3 — SQS',
    '@aws-sdk/client-dynamodb': 'AWS SDK v3 — DynamoDB',
    '@aws-sdk/client-secrets-manager': 'AWS SDK v3 — Secrets Manager',
    '@aws-sdk/client-ssm': 'AWS SDK v3 — SSM',
    '@aws-sdk/client-eventbridge': 'AWS SDK v3 — EventBridge',
    '@aws-sdk/client-ses': 'AWS SDK v3 — SES',
    '@aws-sdk/client-lambda': 'AWS SDK v3 — Lambda (direct invocation)',
    'aws-xray-sdk': 'AWS X-Ray SDK',
    'aws-xray-sdk-core': 'AWS X-Ray SDK Core',
    'aws-lambda-powertools': 'AWS Lambda Powertools (Node)',
}

def analyze_package_json(file_path):
    """Scan package.json for AWS SDK and Lambda-specific dependencies."""
    findings = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        deps = data.get('dependencies', {})
        dev_deps = data.get('devDependencies', {})
        all_deps = {**deps, **dev_deps}

        aws_deps = {}
        aws_sdk_v3_clients = []
        for pkg, version in all_deps.items():
            if pkg in _NODE_AWS_PACKAGES:
                if pkg.startswith('@aws-sdk/'):
                    aws_sdk_v3_clients.append(pkg)
                else:
                    aws_deps[pkg] = {'version': version, 'note': _NODE_AWS_PACKAGES[pkg]}
            # Catch any other @aws-sdk/* clients not in the explicit list
            elif pkg.startswith('@aws-sdk/') or pkg.startswith('@aws-cdk/'):
                aws_sdk_v3_clients.append(pkg)
            elif pkg.startswith('amazon-'):
                aws_deps[pkg] = {'version': version, 'note': 'Amazon-prefixed package'}

        if aws_deps:
            findings['aws_packages'] = aws_deps
        if aws_sdk_v3_clients:
            findings['aws_sdk_v3_clients'] = aws_sdk_v3_clients

        gcp_deps = {k: v for k, v in all_deps.items() if k.startswith('@google-cloud/')}
        if gcp_deps:
            findings['gcp_sdks_present'] = list(gcp_deps.keys())

        if 'node' in data.get('engines', {}):
            findings['node_version'] = data['engines']['node']

    except Exception as e:
        findings['error'] = f"Failed to parse package.json: {e}"
    return findings


# AWS Python package names that signal lock-in
_PYTHON_AWS_PACKAGES = {
    'boto3': 'AWS SDK for Python',
    'botocore': 'AWS SDK core (boto3 dependency)',
    'aws-lambda-powertools': 'AWS Lambda Powertools',
    'aws-cdk-lib': 'AWS CDK library',
    'aws-cdk.core': 'AWS CDK core (v1)',
    'amazon-dax-client': 'DynamoDB Accelerator (DAX) client',
    'aws-xray-sdk': 'AWS X-Ray SDK',
    'chalice': 'AWS Chalice framework (Lambda-specific)',
    'mangum': 'ASGI adapter for AWS Lambda (Mangum)',
    'aws-wsgi': 'WSGI adapter for AWS Lambda',
}

def analyze_requirements_txt(file_path):
    """Scan requirements.txt for AWS SDK and Lambda-specific dependencies."""
    findings = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        aws_packages = {}
        for line in lines:
            line = line.strip()
            # Skip comments and blank lines
            if not line or line.startswith('#'):
                continue
            # Normalize: strip version specifiers to get the base package name
            pkg_name = re.split(r'[>=<!\[;]', line)[0].strip().lower()
            # Check against known AWS packages
            for known_pkg, note in _PYTHON_AWS_PACKAGES.items():
                if pkg_name == known_pkg.lower():
                    aws_packages[pkg_name] = {'raw_line': line, 'note': note}
                    break
            else:
                # Catch any aws- or amazon- prefixed package not in the explicit list
                if pkg_name.startswith('aws-') or pkg_name.startswith('amazon-'):
                    aws_packages[pkg_name] = {'raw_line': line, 'note': 'AWS/Amazon-prefixed package'}

        if aws_packages:
            findings['aws_packages'] = aws_packages

    except Exception as e:
        findings['error'] = f"Failed to parse requirements.txt: {e}"
    return findings

def analyze_iac(file_path):
    findings = {"type": "Unknown", "resources": []}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            if HAS_YAML and file_path.endswith(('.yml', '.yaml')):
                try:
                    data = yaml.safe_load(content)
                    if not data: return {}
                    
                    if 'Resources' in data:
                        findings["type"] = "AWS SAM / CloudFormation"
                        for res_name, res_data in data.get('Resources', {}).items():
                            if isinstance(res_data, dict) and res_data.get('Type') == 'AWS::Serverless::Function':
                                findings["resources"].append(f"SAM Function: {res_name}")
                                events = res_data.get('Properties', {}).get('Events', {})
                                for ev_name, ev_data in events.items():
                                    findings["resources"].append(f"  Trigger -> {ev_data.get('Type')}")
                                    
                    elif 'provider' in data and data['provider'].get('name') == 'aws':
                        findings["type"] = "Serverless Framework"
                        for func_name, func_data in data.get('functions', {}).items():
                            findings["resources"].append(f"SLS Function: {func_name}")
                            for event in func_data.get('events', []):
                                if isinstance(event, dict):
                                    findings["resources"].append(f"  Trigger -> {list(event.keys())[0]}")
                except Exception:
                    pass # Fallback to regex if YAML parsing fails
                    
            if not findings["resources"]:
                # Regex fallback for IaC
                if re.search(r"Type:\s*AWS::Serverless::Function", content):
                    findings["type"] = "AWS SAM (Regex matched)"
                elif re.search(r"provider:\s*\n\s*name:\s*aws", content):
                    findings["type"] = "Serverless Framework (Regex matched)"
                    
    except Exception:
        pass
    return findings if findings.get("type") != "Unknown" else {}


def analyze_cdk(root_dir):
    """
    Detects AWS CDK projects by looking for cdk.json at any level and
    scanning TypeScript/Python stack files for CDK-specific patterns.
    Returns a dict with detected language, stack files, and constructs found.
    """
    findings = {}

    for root, dirs, files in os.walk(root_dir):
        # Skip node_modules and .venv to avoid false positives
        dirs[:] = [d for d in dirs if d not in ('node_modules', '.venv', '__pycache__', 'cdk.out')]

        for file in files:
            path = os.path.join(root, file)

            # cdk.json signals a CDK project root
            if file == 'cdk.json':
                findings.setdefault('cdk_project_roots', []).append(path)
                if HAS_YAML:
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            cdk_config = json.load(f)
                        findings['cdk_app_entry'] = cdk_config.get('app', 'unknown')
                    except Exception:
                        pass

            # TypeScript stack files
            elif file.endswith(('Stack.ts', 'stack.ts')):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    constructs = {}
                    for label, pattern in CDK_PATTERNS.items():
                        if re.search(pattern, content):
                            constructs[label] = True
                    if constructs:
                        findings.setdefault('stack_files', {})[path] = {
                            'language': 'TypeScript',
                            'constructs': list(constructs.keys())
                        }
                except Exception:
                    pass

            # Python stack files
            elif file.endswith(('_stack.py', 'stack.py')):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    constructs = {}
                    for label, pattern in CDK_PATTERNS.items():
                        if re.search(pattern, content):
                            constructs[label] = True
                    if constructs:
                        findings.setdefault('stack_files', {})[path] = {
                            'language': 'Python',
                            'constructs': list(constructs.keys())
                        }
                except Exception:
                    pass

    return findings


def analyze_terraform_aws(file_path):
    """
    Detects AWS Terraform configurations (.tf files) that manage Lambda functions
    and associated infrastructure. Uses regex against HCL since HCL has no
    standard Python parser.
    """
    findings = {"type": "AWS Terraform", "resources": []}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Must reference the AWS provider to be relevant
        is_aws_tf = bool(
            re.search(r'provider\s+["\']aws["\']', content) or
            re.search(r'source\s*=\s*["\']hashicorp/aws["\']', content)
        )
        if not is_aws_tf:
            return {}

        # Extract aws_lambda_function resource names
        for m in re.finditer(r'resource\s+["\']aws_lambda_function["\']\s+["\']([\w-]+)["\']', content):
            findings["resources"].append(f"Lambda Function: {m.group(1)}")
            # Try to extract runtime from the same block
            block_start = m.start()
            block_snippet = content[block_start:block_start + 600]
            runtime_m = re.search(r'runtime\s*=\s*["\']([\w.]+)["\']', block_snippet)
            if runtime_m:
                findings["resources"].append(f"  Runtime: {runtime_m.group(1)}")

        # Extract other AWS resources that require GCP service mapping
        resource_map = {
            "aws_api_gateway_rest_api": "API Gateway",
            "aws_api_gateway_v2_api":   "API Gateway (HTTP)",
            "aws_sns_topic":             "SNS Topic",
            "aws_sqs_queue":             "SQS Queue",
            "aws_dynamodb_table":        "DynamoDB Table",
            "aws_s3_bucket":             "S3 Bucket",
            "aws_iam_role":              "IAM Role",
            "aws_cloudwatch_event_rule": "EventBridge Rule (Cron/Event)",
            "aws_lambda_event_source_mapping": "Lambda Event Source Mapping",
            "aws_lambda_permission":     "Lambda Permission (Trigger)",
            "aws_secretsmanager_secret": "Secrets Manager Secret",
        }
        for tf_type, label in resource_map.items():
            matches = re.findall(
                rf'resource\s+["\']' + re.escape(tf_type) + r'["\']\s+["\']([\w-]+)["\']',
                content
            )
            for name in matches:
                findings["resources"].append(f"{label}: {name}")

    except Exception as e:
        findings["error"] = str(e)

    return findings if findings["resources"] else {}

def print_summary(manifest):
    """Print a human-readable migration summary to stdout."""
    src = manifest['metadata']['source_directory']
    print(f"\n{'='*60}")
    print(f"  Migration Readiness Summary")
    print(f"  Source: {src}")
    print(f"{'='*60}\n")

    # --- IaC Type ---
    iac = manifest.get('iac_analysis', {})
    tf = manifest.get('tf_analysis', {})
    cdk = manifest.get('cdk_analysis', {})
    if iac:
        for path, data in iac.items():
            print(f"📦 IaC: {data.get('type', 'Unknown')} ({os.path.basename(path)})")
            for r in data.get('resources', []):
                print(f"   {r}")
    if tf:
        print(f"📦 IaC: AWS Terraform (.tf files detected)")
        for path, data in tf.items():
            for r in data.get('resources', []):
                print(f"   {r}")
    if cdk:
        roots = cdk.get('cdk_project_roots', [])
        print(f"📦 IaC: AWS CDK (found {len(roots)} project root(s))")
        for stack_path, stack_data in cdk.get('stack_files', {}).items():
            print(f"   Stack [{stack_data['language']}]: {os.path.basename(stack_path)}")
            for c in stack_data.get('constructs', []):
                print(f"     - {c}")
    if not iac and not tf and not cdk:
        print("📦 IaC:  None detected (provide SAM, Serverless, CDK, or .tf files for deeper analysis)")

    # --- Code lock-ins ---
    code = manifest.get('code_analysis', {})
    composer = manifest.get('composer_analysis', {})
    pkg_json = manifest.get('package_json_analysis', {})
    req_txt = manifest.get('requirements_analysis', {})

    all_lock_ins = []
    for path, findings in code.items():
        for label, count in findings.items():
            all_lock_ins.append((os.path.basename(path), label, count))
    for path, findings in composer.items():
        for label, val in findings.items():
            all_lock_ins.append((os.path.basename(path), f"PHP dep — {label}", val))
    for path, findings in pkg_json.items():
        aws_pkgs = findings.get('aws_packages', {})
        v3_clients = findings.get('aws_sdk_v3_clients', [])
        for pkg in list(aws_pkgs.keys()) + v3_clients:
            all_lock_ins.append((os.path.basename(path), f"Node.js dep — {pkg}", 1))
    for path, findings in req_txt.items():
        for pkg in findings.get('aws_packages', {}):
            all_lock_ins.append((os.path.basename(path), f"Python dep — {pkg}", 1))

    if all_lock_ins:
        print(f"\n⚠️  AWS Lock-ins Detected ({len(all_lock_ins)} finding(s)):")
        for fname, label, count in all_lock_ins:
            print(f"   [{fname}] {label}" + (f" ({count} occurrence(s))" if isinstance(count, int) and count > 1 else ""))
    else:
        print("\n✅  No AWS lock-ins detected in code or manifests.")

    # --- Recommended Cloud Run type ---
    print("\n🚀 Recommended Cloud Run target:")
    has_cron = any(
        'cron' in str(data).lower() or 'schedule' in str(data).lower() or 'eventbridge' in str(data).lower()
        for data in list(iac.values()) + list(tf.values())
    )
    if has_cron:
        print("   → Cloud Run JOB  (EventBridge/cron trigger detected — no web server needed)")
        print("   → Cloud Run SERVICE  (if other HTTP triggers also exist)")
    else:
        print("   → Cloud Run SERVICE  (HTTP/API Gateway trigger assumed)")

    print(f"\n{'='*60}\n")


def main(root_dir, output_dir=None, print_human_summary=False):
    print(f"Analyzing directory: {root_dir}")

    # Default output location: current working directory (NOT the source tree)
    if output_dir is None:
        output_dir = os.getcwd()

    manifest = {
        "metadata": {
            "source_directory": os.path.abspath(root_dir),
            "description": "AWS to GCP Cloud Run Migration Manifest"
        },
        "code_analysis": {},
        "composer_analysis": {},
        "package_json_analysis": {},
        "requirements_analysis": {},
        "iac_analysis": {},
        "tf_analysis": {},
        "cdk_analysis": {}
    }

    try:
        for root, _, files in os.walk(root_dir):
            for file in files:
                path = os.path.join(root, file)

                if file.endswith('.py'):
                    findings = analyze_python_ast(path)
                    if findings:
                        manifest["code_analysis"][path] = findings

                elif file.endswith(('.js', '.ts', '.php', '.java', '.go', '.cs')):
                    findings = analyze_generic_regex(path)
                    if findings:
                        manifest["code_analysis"][path] = findings

                elif file == 'composer.json':
                    findings = analyze_composer_json(path)
                    if findings:
                        manifest["composer_analysis"][path] = findings

                elif file == 'package.json':
                    findings = analyze_package_json(path)
                    if findings:
                        manifest["package_json_analysis"][path] = findings

                elif file == 'requirements.txt':
                    findings = analyze_requirements_txt(path)
                    if findings:
                        manifest["requirements_analysis"][path] = findings

                elif file in ('template.yaml', 'template.yml', 'serverless.yml', 'serverless.yaml'):
                    findings = analyze_iac(path)
                    if findings:
                        manifest["iac_analysis"][path] = findings

                elif file.endswith('.tf'):
                    findings = analyze_terraform_aws(path)
                    if findings:
                        manifest["tf_analysis"][path] = findings

        # CDK analysis runs across the whole tree (not per-file)
        cdk_findings = analyze_cdk(root_dir)
        if cdk_findings:
            manifest["cdk_analysis"] = cdk_findings

        manifest_path = os.path.join(output_dir, "migration_manifest.json")
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)

        print(f"\n✅ Analysis complete. Structured report generated at: {manifest_path}")
        print("Agent Instruction: Please read 'migration_manifest.json' to review the findings.")

        if print_human_summary:
            print_summary(manifest)

    except Exception as e:
        print(f"\n❌ Fatal error during analysis: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze an AWS Lambda project for Cloud Run migration readiness."
    )
    parser.add_argument(
        "directory",
        help="Path to the Lambda source directory to analyze."
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Directory where migration_manifest.json will be written. "
             "Defaults to the current working directory."
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        default=False,
        help="Print a human-readable migration summary to stdout after analysis."
    )
    args = parser.parse_args()
    main(args.directory, output_dir=args.output, print_human_summary=args.summary)
