---
name: pytest-linter
description: Guides the agent on how to run clean python styling, Black/Ruff compliance checks, and pytest execution on changed python scripts.
---
# Pytest and Linter Execution Skill

This skill guides you on executing compliant, high-quality testing and linting in Python workspaces.

## Instructions

1.  **Run Linter First**:
    Prior to launching any tests, check if `black` or `ruff` is installed. Run code formatting:
    ```bash
    black src/
    ```
2.  **Execute pytest**:
    Run tests with coverage and verbose logging to capture any regression:
    ```bash
    pytest -v --cov=src/
    ```
3.  **Correct Failures Step-by-Step**:
    Do not rewrite large blocks if tests fail. Isolate the failing test-case and modify only the corresponding modular unit.
