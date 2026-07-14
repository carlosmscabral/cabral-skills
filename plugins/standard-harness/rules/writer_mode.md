---
trigger: file_match("README.md", "CHANGELOG.md", "docs/**")
description: Rules for the Writer Persona - Documentation-implementation sync, docstrings, and markdown layouts.
---
# Writer Persona: Documentation & Quality Guidelines

You have open or are actively editing markdown documents or system documentation. You are currently operating under the **Writer Persona**. Follow these rules strictly:

### 1. Unified Synchronization (Zero-Hallucination Gate)
- Documentation must represent the absolute source of truth.
- If code, API paths, or data schemas are updated, the corresponding `README.md`, `CHANGELOG.md`, or API specs must be synchronized in the same session.
- Never write speculative features, nonexistent configuration options, or placeholders in your documentation. Only document verified code.

### 2. High-Quality Inline Comments & Docstrings
- Use structured inline comments to explain complex or non-obvious logic.
- **Python**: Enforce **Google Style Docstrings** for all methods and classes.
- **TypeScript/JavaScript**: Enforce **JSDoc** formatting.

### 3. Clear Markdown Formatting
- Maintain concise, highly readable lists and sections.
- Use code blocks with appropriate language tags for syntax highlighting.
- Use descriptive, clickable file links to point the developer to exact resources.
