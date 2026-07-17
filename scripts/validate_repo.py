#!/usr/bin/env python3
"""
scripts/validate_repo.py - AI Skills Standards & Repository Enforcement CLI

Validates repository structure, manifests, frontmatter, script permissions,
workspace hygiene, link integrity, vendor digests, and trigger overlaps.

Usage:
  python3 scripts/validate_repo.py [--fix] [--help]
"""

import sys
import os
import re
import json
import stat
import glob
import shutil
import hashlib
import argparse
import urllib.parse


def parse_frontmatter(content):
    """
    Parses YAML frontmatter delimited by initial '---' lines.
    Returns dict of frontmatter key-values, or None if no valid frontmatter block found.
    """
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return None

    fm_lines = []
    end_index = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_index = i
            break
        fm_lines.append(lines[i])

    if end_index == -1:
        return None

    fm_text = "\n".join(fm_lines)

    # Try PyYAML if available
    try:
        import yaml
        data = yaml.safe_load(fm_text)
        if isinstance(data, dict):
            return data
    except ImportError:
        pass

    # Fallback YAML parser for top-level keys
    data = {}
    current_key = None
    val_lines = []
    for line in fm_lines:
        match = re.match(r'^([a-zA-Z0-9_-]+):\s*(.*)$', line)
        if match:
            if current_key:
                data[current_key] = "\n".join(val_lines).strip()
            current_key = match.group(1)
            val = match.group(2).strip()
            if val.startswith(('"', "'")) and val.endswith(('"', "'")) and len(val) >= 2:
                val = val[1:-1]
            val_lines = [val] if val else []
        elif current_key and (line.startswith(" ") or line.startswith("\t") or line.strip() == ""):
            val_lines.append(line.strip())
    if current_key:
        data[current_key] = "\n".join(val_lines).strip()

    return data


def check_manifest_parity(repo_root, fix_mode):
    errors = []
    warnings = []
    plugin_jsons = glob.glob(os.path.join(repo_root, "plugins", "*", "plugin.json"))

    for pj_path in plugin_jsons:
        plugin_dir = os.path.dirname(pj_path)
        plugin_name = os.path.basename(plugin_dir)
        try:
            with open(pj_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            errors.append(f"Plugin manifest {pj_path} is invalid JSON: {e}")
            continue

        for req in ("name", "version"):
            if req not in data:
                errors.append(f"Plugin manifest {pj_path} missing required field '{req}'")

        listed_skills = set(data.get("skills", []))
        skills_dir = os.path.join(plugin_dir, "skills")
        disk_skills = set()
        if os.path.exists(skills_dir) and os.path.isdir(skills_dir):
            disk_skills = {
                d for d in os.listdir(skills_dir)
                if os.path.isdir(os.path.join(skills_dir, d))
            }

        missing_on_disk = listed_skills - disk_skills
        for s in sorted(missing_on_disk):
            errors.append(f"Plugin '{plugin_name}': skill '{s}' listed in plugin.json but {skills_dir}/{s} is missing on disk.")

        unlisted_on_manifest = disk_skills - listed_skills
        for s in sorted(unlisted_on_manifest):
            errors.append(f"Plugin '{plugin_name}': directory {skills_dir}/{s} exists on disk but is not listed in plugin.json.")

    return errors, warnings, []


def check_frontmatter_and_injection(repo_root, fix_mode):
    errors = []
    warnings = []

    skill_mds = glob.glob(os.path.join(repo_root, "skills", "*", "SKILL.md")) + \
                glob.glob(os.path.join(repo_root, "plugins", "*", "skills", "*", "SKILL.md"))

    injection_patterns = [
        "ignore previous instructions",
        "system prompt",
        "disregard prior instructions"
    ]

    for md_path in sorted(skill_mds):
        rel_path = os.path.relpath(md_path, repo_root)
        try:
            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            errors.append(f"Failed to read {rel_path}: {e}")
            continue

        fm = parse_frontmatter(content)
        if not fm:
            errors.append(f"{rel_path}: Missing or malformed YAML frontmatter (must start and end with '---').")
            continue

        for field in ("name", "description"):
            if field not in fm or fm[field] is None or not str(fm[field]).strip():
                errors.append(f"{rel_path}: Frontmatter missing required field '{field}'.")

        desc = str(fm.get("description") or "").lower()
        for pat in injection_patterns:
            if pat in desc:
                errors.append(f"{rel_path}: Prompt injection pattern detected in description: '{pat}'.")

    return errors, warnings, []


def check_script_permissions(repo_root, fix_mode):
    errors = []
    warnings = []
    fixes = []

    search_dirs = [
        os.path.join(repo_root, "scripts"),
    ]

    for root_dir, dirs, files in os.walk(repo_root):
        if "/." in root_dir or "__pycache__" in root_dir:
            continue
        if os.path.basename(root_dir) == "scripts":
            search_dirs.append(root_dir)

    script_files = set()
    for sdir in set(search_dirs):
        if not os.path.exists(sdir):
            continue
        for root, _, files in os.walk(sdir):
            for file in files:
                if file.endswith(".sh") or file.endswith(".py"):
                    script_files.add(os.path.join(root, file))

    for script_path in sorted(script_files):
        rel_path = os.path.relpath(script_path, repo_root)
        st = os.stat(script_path)
        is_exec = bool(st.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))
        if not is_exec:
            if fix_mode:
                new_mode = st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
                os.chmod(script_path, new_mode)
                fixes.append(f"Added executable (+x) bit to {rel_path}")
            else:
                errors.append(f"Script file is not executable (+x): {rel_path}")

    return errors, warnings, fixes


def check_clean_workspace(repo_root, fix_mode):
    errors = []
    warnings = []
    fixes = []

    scan_roots = [
        os.path.join(repo_root, "skills"),
        os.path.join(repo_root, "plugins"),
        os.path.join(repo_root, "scripts")
    ]

    for sroot in scan_roots:
        if not os.path.exists(sroot):
            continue
        for root, dirs, files in os.walk(sroot, topdown=False):
            for d in list(dirs):
                if d == "__pycache__":
                    full_path = os.path.join(root, d)
                    rel_path = os.path.relpath(full_path, repo_root)
                    if fix_mode:
                        shutil.rmtree(full_path)
                        fixes.append(f"Removed directory: {rel_path}")
                        dirs.remove(d)
                    else:
                        errors.append(f"Forbidden directory found: {rel_path}")

            for f in files:
                if f.endswith(".pyc") or f == ".env":
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, repo_root)
                    if fix_mode:
                        os.remove(full_path)
                        fixes.append(f"Removed file: {rel_path}")
                    else:
                        errors.append(f"Forbidden file found: {rel_path}")

    return errors, warnings, fixes


def slugify_heading(heading_text):
    """
    Converts markdown header text to anchor slug (GitHub style).
    """
    text = re.sub(r'`([^`]*)`', r'\1', heading_text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s]+', '-', text)
    return text


def check_link_integrity(repo_root, fix_mode):
    errors = []
    warnings = []

    md_files = [os.path.join(repo_root, "AGENTS.md")] + \
               glob.glob(os.path.join(repo_root, "skills", "*", "SKILL.md")) + \
               glob.glob(os.path.join(repo_root, "plugins", "*", "skills", "*", "SKILL.md"))

    link_regex = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    headings_cache = {}

    def get_headings(file_path):
        if file_path in headings_cache:
            return headings_cache[file_path]
        slugs = set()
        raw_headers = set()
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line_str = line.strip()
                        if line_str.startswith("#"):
                            header_text = line_str.lstrip("#").strip()
                            raw_headers.add(header_text.lower())
                            slugs.add(slugify_heading(header_text))
            except Exception:
                pass
        headings_cache[file_path] = (slugs, raw_headers)
        return slugs, raw_headers

    for md_path in sorted(md_files):
        if not os.path.exists(md_path):
            continue
        rel_src = os.path.relpath(md_path, repo_root)
        try:
            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            errors.append(f"Failed to read {rel_src}: {e}")
            continue

        # Strip code blocks to avoid false link matches inside code snippets
        clean_content = re.sub(r'```[\s\S]*?```', '', content)
        clean_content = re.sub(r'`[^`]*`', '', clean_content)

        for match in link_regex.finditer(clean_content):
            link_text, link_target = match.group(1), match.group(2).strip()
            if link_target.startswith(("http://", "https://", "mailto:", "ftp:")):
                continue

            if link_target.startswith("#"):
                target_file = md_path
                anchor = link_target[1:]
            else:
                parts = link_target.split("#", 1)
                file_part = parts[0]
                anchor = parts[1] if len(parts) > 1 else None
                file_part = urllib.parse.unquote(file_part)
                target_file = os.path.normpath(os.path.join(os.path.dirname(md_path), file_part))

            rel_target = os.path.relpath(target_file, repo_root)

            if not os.path.exists(target_file):
                errors.append(f"{rel_src}: Broken link '{link_target}' -> target '{rel_target}' does not exist.")
            elif anchor and target_file.endswith(".md"):
                slugs, raw_headers = get_headings(target_file)
                clean_anchor = anchor.lower().strip()
                if clean_anchor not in slugs and clean_anchor not in raw_headers:
                    slug_anchor = slugify_heading(anchor)
                    if slug_anchor not in slugs:
                        errors.append(f"{rel_src}: Broken anchor in link '{link_target}' -> anchor '#{anchor}' not found in '{rel_target}'.")

    return errors, warnings, []


def calculate_tree_digest(dir_path):
    """
    Calculates recursive SHA-256 tree digest for a directory.
    Standardized across validate_repo.py and vendor-agents-cli.sh.
    """
    rel_files = []
    for root, dirs, files in os.walk(dir_path):
        dirs[:] = [d for d in dirs if d != "__pycache__" and not d.startswith(".")]
        for f in files:
            if f.endswith(".pyc") or f in (".DS_Store", ".env"):
                continue
            full_p = os.path.join(root, f)
            rel_p = os.path.relpath(full_p, dir_path).replace("\\", "/")
            rel_files.append((rel_p, full_p))

    rel_files.sort(key=lambda x: x[0])
    lines = []
    for rel_p, full_p in rel_files:
        with open(full_p, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        lines.append(f"{rel_p}:{file_hash}\n")

    combined = "".join(lines).encode("utf-8")
    return hashlib.sha256(combined).hexdigest()


def check_vendor_digest_integrity(repo_root, fix_mode):
    errors = []
    warnings = []
    fixes = []

    vendored_json_path = os.path.join(repo_root, "vendored.json")
    if not os.path.exists(vendored_json_path):
        return errors, warnings, fixes

    try:
        with open(vendored_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        errors.append(f"vendored.json is invalid JSON: {e}")
        return errors, warnings, fixes

    json_modified = False
    for key, info in data.items():
        if not isinstance(info, dict):
            continue
        skills = info.get("skills", [])
        recorded_digests = info.get("digests", {})
        new_digests = dict(recorded_digests)

        for skill_name in skills:
            matching_dirs = glob.glob(os.path.join(repo_root, "plugins", "*", "skills", skill_name))
            if not matching_dirs:
                errors.append(f"Vendored skill '{skill_name}' listed in vendored.json not found on disk.")
                continue

            skill_dir = matching_dirs[0]
            current_digest = calculate_tree_digest(skill_dir)
            recorded_digest = recorded_digests.get(skill_name)

            if recorded_digest != current_digest:
                if fix_mode:
                    new_digests[skill_name] = current_digest
                    json_modified = True
                    fixes.append(f"Updated digest for vendored skill '{skill_name}' in vendored.json ({current_digest[:8]}...)")
                else:
                    errors.append(f"Vendor digest mismatch for skill '{skill_name}': calculated {current_digest}, recorded {recorded_digest}")

        if fix_mode and json_modified:
            info["digests"] = new_digests

    if fix_mode and json_modified:
        with open(vendored_json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")

    return errors, warnings, fixes


def check_trigger_overlap(repo_root, fix_mode):
    errors = []
    warnings = []

    skill_mds = glob.glob(os.path.join(repo_root, "skills", "*", "SKILL.md")) + \
                glob.glob(os.path.join(repo_root, "plugins", "*", "skills", "*", "SKILL.md"))

    stop_words = {
        "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "of", "with", "by",
        "is", "are", "was", "were", "be", "been", "being", "this", "that", "these", "those",
        "it", "its", "use", "used", "using", "uses", "skill", "when", "how", "what", "which",
        "who", "whom", "will", "would", "should", "can", "could", "may", "might", "must",
        "from", "into", "over", "after", "before", "between", "under", "again", "further",
        "then", "once", "here", "there", "all", "any", "both", "each", "few", "more", "most",
        "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very"
    }

    negative_phrases = [
        "do not use", "don't use", "negative triggers", "not for", "negative:", "- do not"
    ]

    skill_data = []

    for md_path in sorted(skill_mds):
        rel_path = os.path.relpath(md_path, repo_root)
        skill_name = os.path.basename(os.path.dirname(md_path))
        try:
            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            continue

        fm = parse_frontmatter(content)
        desc = (fm.get("description") or "") if fm else ""

        raw_tokens = re.findall(r'\b[a-z0-9_]+\b', str(desc).lower())
        tokens = {t for t in raw_tokens if t not in stop_words and len(t) > 2}

        content_lower = content.lower()
        has_negative = any(phrase in content_lower for phrase in negative_phrases)

        skill_data.append({
            "name": skill_name,
            "rel_path": rel_path,
            "tokens": tokens,
            "has_negative": has_negative
        })

    for i in range(len(skill_data)):
        for j in range(i + 1, len(skill_data)):
            s1 = skill_data[i]
            s2 = skill_data[j]

            t1, t2 = s1["tokens"], s2["tokens"]
            if not t1 or not t2:
                continue

            intersection = t1 & t2
            union = t1 | t2
            jaccard = len(intersection) / len(union) if union else 0.0

            if jaccard > 0.6:
                if not s1["has_negative"] and not s2["has_negative"]:
                    warnings.append(
                        f"High trigger overlap between '{s1['name']}' and '{s2['name']}' "
                        f"(Jaccard index: {jaccard:.2f}) without negative trigger notes."
                    )

    return errors, warnings, []


def main():
    parser = argparse.ArgumentParser(description="AI Skills Standards & Repository Enforcement CLI")
    parser.add_argument("--fix", action="store_true", help="Auto-repair fixable validation issues")
    args = parser.parse_args()

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    print(f"Running repository validation checks (mode: {'FIX' if args.fix else 'CHECK'})...\n")

    checks = [
        ("Check 1: Manifest Parity", lambda: check_manifest_parity(repo_root, args.fix)),
        ("Check 2: Frontmatter & Injection Scan", lambda: check_frontmatter_and_injection(repo_root, args.fix)),
        ("Check 3: Script Permissions", lambda: check_script_permissions(repo_root, args.fix)),
        ("Check 4: Clean Workspace", lambda: check_clean_workspace(repo_root, args.fix)),
        ("Check 5: Link Integrity", lambda: check_link_integrity(repo_root, args.fix)),
        ("Check 6: Vendor Digest Integrity", lambda: check_vendor_digest_integrity(repo_root, args.fix)),
        ("Check 7: Trigger Overlap Scanner", lambda: check_trigger_overlap(repo_root, args.fix)),
    ]

    total_errors = 0
    total_warnings = 0
    total_fixes = 0

    for title, check_fn in checks:
        print(f"--- {title} ---")
        result = check_fn()
        errors, warnings, fixes = result[0], result[1], result[2]

        total_errors += len(errors)
        total_warnings += len(warnings)
        total_fixes += len(fixes)

        for fix in fixes:
            print(f"  [FIXED] {fix}")
        for err in errors:
            print(f"  [FAIL] {err}")
        for warn in warnings:
            print(f"  [WARN] {warn}")

        if not errors and not warnings and not fixes:
            print("  [PASS] OK")
        print()

    print("Summary:")
    print(f"  Fixes applied: {total_fixes}")
    print(f"  Warnings:      {total_warnings}")
    print(f"  Errors:        {total_errors}")

    if total_errors > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
