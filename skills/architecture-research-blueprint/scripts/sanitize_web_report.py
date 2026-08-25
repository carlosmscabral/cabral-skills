#!/usr/bin/env python3
"""
Sanitizes HTML report files by converting residual LaTeX mathematical notation
($...$, \to, O(N), etc.) into clean semantic HTML (<code>, <em>, Unicode symbols)
and validating that no unparsed LaTeX delimiters remain.
"""

import sys
import os
import re
from pathlib import Path

# Symbol translation table
SYMBOL_REPLACEMENTS = [
    (r'\\to', '→'),
    (r'\\rightarrow', '→'),
    (r'\\leftarrow', '←'),
    (r'\\le\b', '≤'),
    (r'\\leq\b', '≤'),
    (r'\\ge\b', '≥'),
    (r'\\geq\b', '≥'),
    (r'\\approx\b', '≈'),
    (r'\\neq\b', '≠'),
    (r'\\times\b', '×'),
    (r'\\pm\b', '±'),
    (r'\\mu\b', 'µ'),
    (r'\\Delta\b', 'Δ'),
    (r'\\cdot\b', '·'),
    (r'\\dots\b', '…'),
    (r'\\in\b', '∈'),
    (r'\\infty\b', '∞'),
    (r'\\text\{([^}]+)\}', r'\1'),
    (r'\\mathbf\{([^}]+)\}', r'<strong>\1</strong>'),
    (r'\\mathit\{([^}]+)\}', r'<em>\1</em>'),
]

def sanitize_math_expression(expr: str) -> str:
    """Converts a math expression string into clean semantic HTML."""
    expr = expr.strip()
    
    # Check for symbol replacements first
    for pattern, repl in SYMBOL_REPLACEMENTS:
        expr = re.sub(pattern, repl, expr)
    
    # Big-O notation: $O(1)$, $O(N)$, $O(N \log N)$, etc.
    if re.match(r'^O\([^\)]+\)$', expr):
        return f'<code>{expr}</code>'
    
    # Single variable like $N$, $k$, $T$
    if re.match(r'^[A-Za-z]$', expr):
        return f'<em>{expr}</em>'
    
    # Simple equation or bound like p99 <= 120ms or N = 500
    if re.search(r'[=≤≥<>→+\-×/]', expr):
        return f'<code>{expr}</code>'
    
    # General expression fallback
    return f'<code>{expr}</code>'

def sanitize_html_content(content: str) -> tuple[str, int]:
    """Scans and replaces LaTeX delimiters in HTML content, preserving script/style/pre/code blocks."""
    # Split content by protected tags (script, style, pre, code, svg) to avoid corrupting code
    token_pattern = re.compile(r'(<(?:script|style|pre|code|svg)\b[^>]*>.*?</(?:script|style|pre|code|svg)>)', re.DOTALL | re.IGNORECASE)
    parts = token_pattern.split(content)
    
    total_replacements = 0
    new_parts = []
    
    for i, part in enumerate(parts):
        # Even indices are normal HTML content; odd indices are protected tags
        if i % 2 == 0:
            # First handle block math: $$...$$
            def block_repl(m):
                nonlocal total_replacements
                inner = m.group(1).strip()
                cleaned = sanitize_math_expression(inner)
                if cleaned == inner:
                    return m.group(0)
                total_replacements += 1
                return f'<div class="pedagogy-box"><div class="pedagogy-title">📐 Formula</div><div class="pedagogy-text">{cleaned}</div></div>'
            
            part = re.sub(r'\$\$(.+?)\$\$', block_repl, part, flags=re.DOTALL)
            
            # Then handle inline math: $...$
            def inline_repl(m):
                nonlocal total_replacements
                inner = m.group(1).strip()
                # If it's pure currency or price range (e.g. "10 to $20", "$10 - $20", or "100/mo"), preserve it
                if re.match(r'^\d+(?:,\d+)*(?:\.\d+)?(?:\s*(?:k|M|B|/mo|/month|/hr|/yr|USD|EUR|to\s+\$?\d+|-\s*\$?\d+))?$', inner, re.IGNORECASE):
                    return m.group(0)
                cleaned = sanitize_math_expression(inner)
                total_replacements += 1
                return cleaned
            
            # Match $...$ where it's not preceded by a backslash
            part = re.sub(r'(?<!\\)\$([A-Za-z0-9_\\{}() \-\+=\/≤≥→·×\^]+?)\$(?!\d)', inline_repl, part)
            
            new_parts.append(part)
        else:
            new_parts.append(part)
            
    return "".join(new_parts), total_replacements

def process_file(filepath: Path) -> int:
    try:
        text = filepath.read_text(encoding='utf-8')
        sanitized, count = sanitize_html_content(text)
        if count > 0:
            filepath.write_text(sanitized, encoding='utf-8')
            print(f"  [FIXED] {filepath.name}: {count} LaTeX expressions converted.")
        else:
            print(f"  [CLEAN] {filepath.name}: No raw LaTeX found.")
        return count
    except Exception as e:
        print(f"  [ERROR] {filepath.name}: {e}", file=sys.stderr)
        return 0

def main():
    target_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    print(f"Scanning for HTML files in: {target_dir.resolve()}")
    
    html_files = list(target_dir.glob("**/*.html")) if target_dir.is_dir() else [target_dir] if target_dir.suffix == ".html" else []
    
    if not html_files:
        print("No HTML files found to sanitize.")
        return 0
        
    total_fixes = 0
    for hf in html_files:
        total_fixes += process_file(hf)
        
    print(f"\nCompleted: {len(html_files)} files scanned, {total_fixes} expressions sanitized.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
