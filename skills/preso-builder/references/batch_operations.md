# gslides Batch Operations & Payload Compilation Reference

This document provides a comprehensive reference for assembling single-pass atomic JSON payloads for `/google/bin/releases/gemini-agents-gslides/gslides batch`.

---

### 1. The Single-Pass Batch Architecture

The Google Slides API natively rejects multi-operation requests if an operation references an `objectId` that does not yet exist. However, the `gslides` CLI supports **client-side placeholder ID resolution**:

```
[ In-Memory Batch Manifest ]
  │
  ├─ 1. {"op": "add-slide", "layout": "BLANK", "id": "SLIDE_01"}
  ├─ 2. {"op": "set-background", "slide": "SLIDE_01", "color": "#1E2761"}
  ├─ 3. {"op": "add-textbox", "slide": "SLIDE_01", "text": "...", "id": "TITLE_01"}
  └─ 4. {"op": "set-notes", "slide": "SLIDE_01", "text": "Speaker notes..."}
```

* The CLI creates the slide, discovers its API-generated ID (e.g. `g3eaafbbd7f6_0_12`), replaces all occurrences of `"SLIDE_01"` in subsequent operations, and automatically defers `set-notes` to a clean second-pass call.

---

### 2. Default Slide Cleanup Rule

Newly created presentations via `gslides create` contain a single default title slide (`p`) with centered placeholders `i0` and `i1`. When constructing new presentations from scratch, the batch compiler **must** delete these default elements first:

```json
[
  {"op": "delete-element", "element": "i0"},
  {"op": "delete-element", "element": "i1"}
]
```

When cloning a master template presentation (`gslides copy`), custom slide layouts are preserved and default blank slides are added cleanly using `"layout": "BLANK"`.

---

### 3. Complete Batch Operations Reference Table

| Operation (`op`) | Mandatory Fields | Optional / Styling Fields | Description |
| :--- | :--- | :--- | :--- |
| `add-slide` | `layout`, `id` | `insertion_index` | Adds a new slide. Default: `BLANK`. `id` sets a placeholder ID for later ops. |
| `set-background`| `slide`, `color` | — | Sets slide background hex color (e.g. `"#1E2761"`). |
| `add-textbox` | `slide`, `text`, `x`, `y`, `width`, `height` | `font_size`, `bold`, `italic`, `color`, `font_family`, `alignment`, `content_alignment`, `line_spacing`, `background_color`, `alpha`, `link`, `id` | Creates a text box with full styling and alignment. |
| `add-shape` | `slide`, `shape_type`, `x`, `y`, `width`, `height` | `background_color`, `alpha`, `id` | Creates vector shapes (`RECTANGLE`, `ROUND_RECTANGLE`, `ELLIPSE`, etc.). |
| `style-shape` | `element` | `background_color`, `alpha`, `outline_color`, `outline_weight` | Styles fill, border stroke color, and line weight. |
| `add-line` | `slide`, `x`, `y`, `width`, `height` | `line_category`, `start_arrow`, `end_arrow`, `line_weight`, `color`, `dash_style`, `start_connect`, `end_connect`, `id` | Creates straight lines, chevrons, or auto-routed connected arrows between shapes. |
| `add-table` | `slide`, `rows`, `cols`, `id` | `x`, `y`, `width`, `height` | Creates an $R \times C$ data grid table. |
| `set-table-cell`| `table`, `row`, `col`, `text` | `color`, `bold`, `font_size`, `font_family`, `background_color`, `alpha` | Inserts and styles text inside a table cell. |
| `set-notes` | `slide`, `text` | — | Attaches speaker notes to a slide. Automatically resolved for placeholder slides. |
| `delete-element`| `element` | — | Deletes an element by ID (e.g. `i0`, `i1`). |
| `update-text` | `element`, `text` | — | Replaces all text in an existing element. |
| `add-text` | `element`, `text` | — | Appends text into an existing shape or placeholder. |
| `style-text` | `element` | `color`, `bold`, `font_size`, `font_family`, `start`, `end` | Restyles a character range in existing text. |

---

### 4. Shape Types & Vertical Alignments

#### Supported Shape Types (`shape_type`)
* `RECTANGLE`: Sharp 90-degree rectangle (used for top accent stripes, divider rules, and left indicator bars).
* `ROUND_RECTANGLE`: Rounded card container (used for cards, pills, code windows, and CTA buttons).
* `ELLIPSE`: Circular badge indicator or traffic light dot.

#### Vertical Content Alignment (`content_alignment`)
* `TOP`: Text anchored to the top margin of the textbox. (Standard for card bodies, code terminal text, and bullet lists).
* `MIDDLE`: Text vertically centered in the textbox. (Standard for category pills, badge labels, and CTA buttons).
* `BOTTOM`: Text anchored to the bottom.

---

### 5. Line Connectors & Flow Diagram Routing

For Archetype 5 (`ladder_hierarchy`), directional flow is created using connected lines or chevron text characters:

```json
{
  "op": "add-line",
  "slide": "SLIDE_01",
  "line_category": "STRAIGHT",
  "x": 187,
  "y": 220,
  "width": 16,
  "height": 0,
  "end_arrow": "FILL_ARROW",
  "color": "#1A73E8",
  "line_weight": 2.0
}
```
