---
name: sec-auditor
description: Guides the agent on executing static security scanning, auditing code for shell injections, and verifying API credential masks.
---
# Static Security Auditing Skill

This skill outlines how to check codebases for security vulnerabilities, exposed secrets, and unmasked environment variables.

## Guidelines

1.  **Credential Sweep**:
    Scan files for raw credentials or key strings using regex patterns or tools:
    ```bash
    grep -E "API_KEY|SECRET|PASSWORD" src/
    ```
2.  **Verify Shell Injection Safety**:
    Inspect all usages of subprocess executions to ensure user inputs are never concatenated directly into shell strings (always use raw lists without `shell=True`).
3.  **Confirm Dependency Locks**:
    Verify that lockfiles (`package-lock.json`, `poetry.lock`) exist and are validated against approved enterprise hash databases.
