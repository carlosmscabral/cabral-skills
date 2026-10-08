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

> **Blueprint template:** it has no `i0`/`i1`, so `--clean-placeholders` fails with **HTTP 400**. Leave it off. `preso build` records the template's own slides before the batch and deletes them afterward.

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
| `style-text` | `element` | `color`, `bold`, `font_size`, `font_family`, `start`, `end` | Restyles a character range in existing text. **Ignores `line_spacing`**, which you can only set at `add-textbox` time. |
| `add-image` | `slide`, `url`, `x`, `y`, `width`, `height` | — | Inserts an image from a URL. Aspect ratio is preserved inside the box. |
| `skip-slide` / `unskip-slide` | `slide` | — | Hides or unhides a slide in presentation mode. `preso` emits `skip-slide` for `appendix`, `skip: true`, and tiers not shown at `--duration`. These ops exist even though `--help` doesn't list them. |
| `_pending-image` | *(internal)* | — | Never sent to gslides. `image_split` emits it for local files, and the compiler lifts it into `BatchResult.pending_images`. |

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

---

### 6. `resolved_ids`, Local Images & Surgical Edits

* `gslides batch --json` returns `{"created_slides": [...], "resolved_ids": {"SLIDE_01": "g3ea…_0_12", …}}`.
  Use `resolved_ids` for any follow-up command that targets a slide you just created.
* Local image files can't go through the batch. After the batch runs, `preso build` calls
  `gslides mutate insert-image-from-file <deck> --slide <resolved_id> --file <png> --x --y --width --height`.
* Pathway C (surgical edits on a built deck), known quirks:
  * `resize-element` takes a **scale factor**, not target points.
  * `move-element` **resets scale**, so move first and then resize.
  * Text ranges (`start`/`end`) are **UTF-16** code units. Characters outside the BMP (most emoji)
    count as 2. Avoid them in visible text.
  * The next `preso build` overwrites manual edits, so put durable changes back into the spec.

---

### 7. Native diagrams (raw-batch)

`flow_diagram` slides need things the `batch` op schema can't express: several text
styles in one box, paragraph spacing, and connectors glued to shapes. So the build runs in
two atomic steps:

1. `gslides batch` creates the slide, header and notes (`resolved_ids` maps the slide).
2. `gslides mutate raw-batch <deck> -f req.json` draws the diagram with raw Slides API
   requests: `createShape` + `updateShapeProperties`, `insertText` + `updateTextStyle`
   (one per run, UTF-16 ranges) + `updateParagraphStyle`, `createLine` (`CURVED` for loops)
   + `updateLineProperties` with `startConnection`/`endConnection`.

The compiler emits a `_raw-requests` marker per slide → `BatchResult.raw_requests`; the CLI
retargets `pageObjectId` to the resolved slide ID and suffixes every element ID per build
(`retarget_requests`), so rebuilding into an existing deck can't collide.

Rules that make it work (learned the hard way):

* **Choose your own objectIds** (≥5 chars, `[A-Za-z0-9_-:]`), so one batch can create and then
  style/connect elements with no read-back pass. The batch is **atomic**: one bad request
  (e.g. a 4-char ID, or styling an empty text box) and nothing is applied.
* **Connection sites** on `RECTANGLE`/`ROUND_RECTANGLE`: 0 top, 1 left, 2 bottom, 3 right.
  Glued `CURVED` lines render along the connection, so the line's own box only needs to be
  approximate. No `rerouteLine` needed.
* **UTF-16 indices.** Measure runs with `len(s.encode("utf-16-le")) // 2`. Emoji outside the BMP
  (📍) count as 2 and render unreliably (invisible on a same-colour fill), so the engine strips
  them. Use `✓ ● ○ → ↻`.
* **Fresh decks:** `mutate create --json` prints plain text, so parse `(ID: …)`. The first slide
  is `p`, with placeholders `i0`/`i1`. Prepend `deleteObject` for both to the same batch.
* **Notes** go via `set-notes` (or the deck batch), not raw requests.
* **Incremental patch:** to fix one element, send `deleteObject` + only the requests whose
  `objectId` is that element (`diagrams.filter_requests_for`, or `--patch` in
  [examples/diagram_slide_rawbatch.py](../examples/diagram_slide_rawbatch.py)). No full redraw.
* **Never edit someone else's shared deck.** Create a new deck and offer the copy.
