# Mandatory Standards for Interactive Web Reports & Mermaid.js

This document provides strict, battle-tested engineering standards for generating interactive architectural web reports, preventing layout collapse, avoiding Mermaid.js parsing errors, and guaranteeing high-resolution visual exploration.

---

## 1. Zero-Defect Mermaid.js Syntax Rules

### A. Subgraph Styling Prohibitions
- **Rule:** NEVER append CSS classes to a subgraph declaration.
- **Wrong:** `subgraph ID ["Title"]:::className` (causes immediate parse error in Mermaid 10+).
- **Correct:** Apply classes strictly to child nodes inside the subgraph:
  ```mermaid
  subgraph ClusterA ["Cluster Alpha"]
      Node1["Service Pod"]:::blueNode
  end
  ```

### B. Subgraph Connection Prohibitions
- **Rule:** NEVER draw arrows/edges directly to or from a subgraph identifier.
- **Wrong:** `SubgraphA --> SubgraphB` (crashes dagre-d3 layout engine).
- **Correct:** Connect real child nodes to real child nodes: `NodeA1 --> NodeB1`.

### C. Sequence Diagram Semicolon Prohibitions
- **Rule:** NEVER use semicolons (`;`) in sequence diagram message text.
- **Wrong:** `Client ->> DB: BEGIN TRANSACTION; SELECT * FROM table;`
- **Correct:** `Client ->> DB: BEGIN TRANSACTION - SELECT * FROM table`

### D. Safe Character Labeling
- **Rule:** Always wrap edge labels with special characters (colons, slashes, brackets) in double quotes:
  - `NodeA -->|"HTTPS / Port 443"| NodeB`

### E. Orientation: Prefer Top-Down (`graph TD`) for Dense Sequences
- **Rule:** Wide timelines or multi-step processes with descriptive text should use `graph TD` (vertical).
- **Why:** `graph LR` (horizontal) creates extremely wide diagrams that get shrunk vertically into unreadable slivers when constrained to responsive card containers.

---

## 2. Frontend Rendering Architecture (`app.js`)

### A. Avoid `startOnLoad: true` inside `DOMContentLoaded`
Mermaid 10.x fails to render if `startOnLoad: true` is initialized after `DOMContentLoaded` has already fired, or if a single diagram contains a syntax flaw.

### B. Individual Async Rendering Loop with Error Isolation
```javascript
async function renderMermaidDiagrams() {
  if (!window.mermaid) {
    let retries = 0;
    const interval = setInterval(async () => {
      retries++;
      if (window.mermaid) {
        clearInterval(interval);
        await doRender();
      } else if (retries > 30) {
        clearInterval(interval);
        console.error('Timeout loading Mermaid.js from CDN.');
      }
    }, 150);
    return;
  }
  await doRender();

  async function doRender() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    mermaid.initialize({
      startOnLoad: false,
      theme: isDark ? 'dark' : 'neutral',
      securityLevel: 'loose',
      fontFamily: 'Google Sans, Inter, sans-serif'
    });

    const nodes = document.querySelectorAll('.mermaid');
    for (let i = 0; i < nodes.length; i++) {
      const el = nodes[i];
      if (!el.hasAttribute('data-raw-code')) {
        el.setAttribute('data-raw-code', el.textContent.trim());
      }
      const rawCode = el.getAttribute('data-raw-code');
      try {
        const uniqueId = `mermaid-svg-${Date.now()}-${i}`;
        const { svg, bindFunctions } = await mermaid.render(uniqueId, rawCode);
        el.innerHTML = svg;
        if (bindFunctions) bindFunctions(el);
      } catch (err) {
        console.error(`Error rendering Mermaid #${i + 1}:`, err);
        el.innerHTML = `<div class="diagram-error">⚠️ Erro de Renderização: ${err.message}</div>`;
      }
    }
  }
}
```

---

## 3. Universal Fullscreen Lightbox Modal (Zoom & Pan)

Every architectural report must equip diagrams with interactive zoom capabilities:
1. **Trigger:** Floating `🔍 Expandir / Zoom` button on hover + click-to-open on diagram containers.
2. **Modal Viewport:** High-contrast, backdrop-blurred fullscreen container (`95vw` × `92vh`).
3. **Controls:**
   - Zoom In (`+` / step +0.25x)
   - Zoom Out (`-` / step -0.25x)
   - Reset (`100%`)
   - Fit to Screen
4. **Interaction:**
   - Mouse click-and-drag pan (`grabbing` cursor).
   - Scroll wheel zoom centered on cursor.
   - Keyboard shortcuts: <kbd>ESC</kbd> to close, <kbd>+</kbd>/<kbd>-</kbd> for zoom, <kbd>0</kbd> to reset.

---

## 4. Typography & Mathematical Representation Contract

Never transport raw LaTeX math notations (`$...$`, `$\to$`, `$$...$$`) directly into vanilla HTML files.

### A. Two-Tier Defense-in-Depth Architecture

To permanently prevent LaTeX residue in web reports, use a 2-tier defense:

1. **Tier 1 (Build / Scaffolding Time):** Execute the sanitization script on all generated HTML files:
   ```bash
   python3 skills/architecture-research-blueprint/scripts/sanitize_web_report.py path/to/web_report/
   ```
2. **Tier 2 (Client-Side DOM Fallback):** The included `app.js` automatically runs `autoCleanDomMath()` on `DOMContentLoaded`, intercepting any residual `$math$` strings in text nodes and dynamically converting them to semantic HTML tags before display.

### B. Canonical Translation Reference Table

| Raw LaTeX in Markdown | Clean Semantic HTML / Unicode | Target Visual Display |
|---|---|---|
| `$\to$` or `\rightarrow` | `→` | Inline arrow `→` |
| `$\leftarrow$` | `←` | Inline arrow `←` |
| `$O(1)$`, `$O(N)$`, `$O(N \log N)$` | `<code>O(1)</code>`, `<code>O(N)</code>` | Monospace badge `O(1)` |
| `$N$`, `$k$`, `$T$` (single vars) | `<em>N</em>`, `<em>k</em>`, `<em>T</em>` | Italic variable *N* |
| `$p99 \le 120\text{ms}$` | `<code>p99 ≤ 120ms</code>` | Formatted constraint |
| `\ge`, `\le`, `\approx`, `\neq` | `≥`, `≤`, `≈`, `≠` | Native Unicode symbols |
| `\times`, `\cdot`, `\dots` | `×`, `·`, `…` | Native typography |
| `$$\text{Formula...}$$` | `<div class="pedagogy-box"><div class="pedagogy-title">📐 Fórmula</div><div class="pedagogy-text"><code>...</code></div></div>` | Styled pedagogical card |

### C. Automated Pre-Publish Checklist
- [ ] Run `python3 .../sanitize_web_report.py web_report/` after consolidating HTML sections.
- [ ] Verify that unescaped `$` only appears in currency notation (e.g. `$100/mês`) and not around code identifiers.
- [ ] Ensure `app.js` contains `autoCleanDomMath()` for runtime safety.
