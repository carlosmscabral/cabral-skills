"""Archetype 11: Flow Diagram — native, editable diagrams via raw Slides API requests.

`gslides batch` cannot express multi-run text styling, paragraph spacing or
connector lines glued to shapes, which is what makes a process diagram look
designed rather than assembled. This module lays out three diagram families
and emits **raw Slides API requests** (`createShape`, `insertText`,
`updateTextStyle`, `createLine` + `startConnection`/`endConnection`, ...):

- ``timeline`` — N stage cards (top colour bar, kicker, title, lead, body,
  status chip) joined by arrows.
- ``cycle`` — continuous loop of 3-4 nodes on a tinted panel, curved
  clockwise connectors, centre caption, optional entry node + dashed feeder.
  Up to 2 ``stages`` can sit on the left (foundation → loop), which is the
  "where we are" story slide.
- ``funnel`` — chevron strip (one chevron per step, optional active step)
  with a description card under each step.

Shared components: "WE ARE HERE" marker pill, status chips, honesty note
("Today: X mature · Y in progress").

The deck batch creates the slide + header + notes; the diagram body travels
as a ``_raw-requests`` marker that the compiler lifts into
``BatchResult.raw_requests``. After the batch runs, the CLI retargets the
requests at the resolved slide ID (``retarget_requests``) and sends them in a
single atomic ``gslides mutate raw-batch`` call.
"""

from __future__ import annotations

import math
import re
from typing import Any, Optional

from preso.engine.text_fit import (
    CHAR_WIDTH_PROPORTIONAL,
    LINE_HEIGHT_FACTOR,
    TEXTBOX_INNER_PADDING,
)

# =============================================================================
# Diagram design tokens (mirrors references/diagram_tokens.yaml)
# =============================================================================
FONT = "Google Sans"

C_DARK = "#202124"
C_GREY = "#5F6368"
C_FAINT = "#9AA0A6"
C_RULE = "#DADCE0"
C_WHITE = "#FFFFFF"
C_PANEL = "#E8F0FE"

# name -> (accent fill, accessible text-on-light, tint)
ACCENTS: dict[str, tuple[str, str, str]] = {
    "red": ("#EA4335", "#C5221F", "#FCE8E6"),
    "yellow": ("#FBBC04", "#E37400", "#FEF7E0"),
    "blue": ("#4285F4", "#1967D2", "#E8F0FE"),
    "green": ("#34A853", "#137333", "#E6F4EA"),
    "grey": ("#80868B", "#3C4043", "#F1F3F4"),
}
ACCENT_ORDER = ("red", "yellow", "blue", "green")

# status -> (default label, chip fill, chip text)
STATUS_STYLES: dict[str, tuple[str, str, str]] = {
    "done": ("✓ Done", "#E6F4EA", "#137333"),
    "active": ("● In progress", "#E8F0FE", "#1967D2"),
    "next": ("○ Next", "#F1F3F4", "#5F6368"),
    "risk": ("! At risk", "#FCE8E6", "#C5221F"),
}
STATUS_ALIASES = {
    "complete": "done", "completed": "done", "concluido": "done", "concluído": "done",
    "in_progress": "active", "wip": "active", "doing": "active", "current": "active",
    "planned": "next", "todo": "next", "later": "next",
    "blocked": "risk", "at_risk": "risk",
}

# Type scale (pt)
SZ_KICKER = 8.0
SZ_CARD_TITLE = 13.0
SZ_LEAD = 9.0
SZ_BODY = 8.5
SZ_NODE_TITLE = 9.5
SZ_NODE_BODY = 7.5
SZ_PILL = 8.0
SZ_CHIP = 8.5
SZ_NOTE = 7.5
SZ_LABEL = 8.0

# Content region under the standard deck header (header ends ~y=94).
X0, X1 = 36.0, 684.0
Y0, Y1 = 100.0, 376.0
MID_Y = 240.0

LAYOUTS = ("timeline", "cycle", "funnel")
PILL_CHAR_W = 0.56  # em-fraction per char for bold, caps-heavy single-line labels
MAX_STAGES = {"timeline": 5, "cycle": 2}
MIN_OBJECT_ID_LEN = 5
_ID_SAFE = re.compile(r"[^A-Za-z0-9_\-:]")
_NON_BMP = re.compile(r"[\U00010000-\U0010FFFF]")


# =============================================================================
# Low-level raw request helpers
# =============================================================================
def rgb(hex_color: str) -> dict[str, float]:
    h = hex_color.lstrip("#")
    return {"red": int(h[0:2], 16) / 255, "green": int(h[2:4], 16) / 255, "blue": int(h[4:6], 16) / 255}


def u16(text: str) -> int:
    """Length in UTF-16 code units — the unit Slides text indices use."""
    return len(text.encode("utf-16-le")) // 2


def strip_non_bmp(text: str) -> str:
    """Drops astral-plane characters (most emoji). They render unreliably
    (invisible on same-colour fills) and are a common source of index bugs."""
    return _NON_BMP.sub("", text)


def non_bmp_chars(text: str) -> list[str]:
    return _NON_BMP.findall(text or "")


Run = tuple[str, float, bool, str]  # (text, size, bold, color)


class RawCanvas:
    """Accumulates raw Slides API requests for one page.

    Object IDs are ``<prefix>_<name>``, sanitised and padded to the API's
    5-char minimum. Every text box is also recorded with its geometry so the
    validator can run fit checks without touching the API.
    """

    def __init__(self, page_id: str, prefix: str) -> None:
        self.page_id = page_id
        self.prefix = prefix
        self.requests: list[dict[str, Any]] = []
        self.text_boxes: list[dict[str, Any]] = []
        self._ids: set[str] = set()

    # -- ids -----------------------------------------------------------------
    def oid(self, name: str) -> str:
        raw = _ID_SAFE.sub("_", f"{self.prefix}_{name}")
        if raw[0] in "-:":
            raw = "d" + raw
        while len(raw) < MIN_OBJECT_ID_LEN:
            raw += "_"
        if raw in self._ids:
            raise ValueError(f"Duplicate diagram objectId: {raw}")
        self._ids.add(raw)
        return raw

    def _geom(self, x: float, y: float, w: float, h: float) -> dict[str, Any]:
        return {
            "pageObjectId": self.page_id,
            "size": {"width": {"magnitude": round(w, 2), "unit": "PT"},
                     "height": {"magnitude": round(h, 2), "unit": "PT"}},
            "transform": {"scaleX": 1, "scaleY": 1, "translateX": round(x, 2),
                          "translateY": round(y, 2), "unit": "PT"},
        }

    # -- primitives ------------------------------------------------------------
    def shape(self, name: str, kind: str, x: float, y: float, w: float, h: float,
              fill: Optional[str] = None, outline: Optional[str] = None, weight: float = 1.0,
              dash: Optional[str] = None, valign: str = "TOP") -> str:
        oid = self.oid(name)
        self.requests.append({"createShape": {"objectId": oid, "shapeType": kind,
                                              "elementProperties": self._geom(x, y, w, h)}})
        props: dict[str, Any] = {}
        fields: list[str] = []
        if fill:
            props["shapeBackgroundFill"] = {"solidFill": {"color": {"rgbColor": rgb(fill)}, "alpha": 1.0}}
            fields.append("shapeBackgroundFill")
        elif kind != "TEXT_BOX":
            props["shapeBackgroundFill"] = {"propertyState": "NOT_RENDERED"}
            fields.append("shapeBackgroundFill")
        if outline:
            o: dict[str, Any] = {"outlineFill": {"solidFill": {"color": {"rgbColor": rgb(outline)}}},
                                 "weight": {"magnitude": weight, "unit": "PT"}}
            if dash:
                o["dashStyle"] = dash
            props["outline"] = o
        else:
            props["outline"] = {"propertyState": "NOT_RENDERED"}
        fields.append("outline")
        props["contentAlignment"] = valign
        fields.append("contentAlignment")
        self.requests.append({"updateShapeProperties": {"objectId": oid, "shapeProperties": props,
                                                        "fields": ",".join(fields)}})
        return oid

    def text(self, oid: str, runs: list[Run], align: str = "START", spacing: float = 100,
             space_below: float = 0) -> None:
        runs = [(strip_non_bmp(t), s, b, c) for t, s, b, c in runs]
        runs = [r for r in runs if r[0]]
        # Trailing newline on the last run would leave an empty styled paragraph.
        if runs and runs[-1][0].endswith("\n"):
            t, s, b, c = runs[-1]
            runs[-1] = (t.rstrip("\n"), s, b, c)
            runs = [r for r in runs if r[0]]
        full = "".join(r[0] for r in runs)
        if not full.strip():
            return  # Slides rejects styling an empty text box (HTTP 400).
        self.requests.append({"insertText": {"objectId": oid, "text": full}})
        i = 0
        for t, size, bold, color in runs:
            n = u16(t)
            self.requests.append({"updateTextStyle": {
                "objectId": oid,
                "textRange": {"type": "FIXED_RANGE", "startIndex": i, "endIndex": i + n},
                "style": {"fontFamily": FONT, "fontSize": {"magnitude": size, "unit": "PT"}, "bold": bold,
                          "foregroundColor": {"opaqueColor": {"rgbColor": rgb(color)}}},
                "fields": "fontFamily,fontSize,bold,foregroundColor"}})
            i += n
        self.requests.append({"updateParagraphStyle": {
            "objectId": oid, "textRange": {"type": "ALL"},
            "style": {"alignment": align, "lineSpacing": spacing,
                      "spaceAbove": {"magnitude": 0, "unit": "PT"},
                      "spaceBelow": {"magnitude": space_below, "unit": "PT"}},
            "fields": "alignment,lineSpacing,spaceAbove,spaceBelow"}})

    def box(self, name: str, x: float, y: float, w: float, h: float, runs: list[Run],
            align: str = "START", valign: str = "TOP", kind: str = "TEXT_BOX",
            spacing: float = 100, space_below: float = 0, label: str = "",
            single_line: bool = False, **shape_kw: Any) -> str:
        oid = self.shape(name, kind, x, y, w, h, valign=valign, **shape_kw)
        self.text(oid, runs, align, spacing, space_below)
        self.text_boxes.append({"id": oid, "label": label or name, "runs": runs, "w": w, "h": h,
                                "spacing": spacing, "space_below": space_below,
                                "single_line": single_line})
        return oid

    def line(self, name: str, x: float, y: float, w: float, h: float, color: str = C_GREY,
             weight: float = 1.25, start: Optional[str] = None, end: Optional[str] = "FILL_ARROW",
             category: str = "STRAIGHT", conn: Optional[tuple[tuple[str, int], tuple[str, int]]] = None,
             dash: Optional[str] = None) -> str:
        oid = self.oid(name)
        self.requests.append({"createLine": {"objectId": oid, "lineCategory": category,
                                             "elementProperties": self._geom(x, y, max(w, 0.01), max(h, 0.01))}})
        lp: dict[str, Any] = {"lineFill": {"solidFill": {"color": {"rgbColor": rgb(color)}}},
                              "weight": {"magnitude": weight, "unit": "PT"},
                              "endArrow": end or "NONE", "startArrow": start or "NONE"}
        fields = "lineFill,weight,endArrow,startArrow"
        if dash:
            lp["dashStyle"] = dash
            fields += ",dashStyle"
        if conn:
            (a, sa), (b, sb) = conn
            lp["startConnection"] = {"connectedObjectId": a, "connectionSiteIndex": sa}
            lp["endConnection"] = {"connectedObjectId": b, "connectionSiteIndex": sb}
            fields += ",startConnection,endConnection"
        self.requests.append({"updateLineProperties": {"objectId": oid, "lineProperties": lp, "fields": fields}})
        return oid


# Connection sites on RECTANGLE / ROUND_RECTANGLE: 0 top, 1 left, 2 bottom, 3 right.
SITE_TOP, SITE_LEFT, SITE_BOTTOM, SITE_RIGHT = 0, 1, 2, 3


def retarget_requests(requests: list[dict[str, Any]], page_map: dict[str, str],
                      suffix: str = "") -> list[dict[str, Any]]:
    """Points requests at real page IDs and makes element IDs build-unique.

    - ``pageObjectId`` (and an ``objectId`` equal to a page placeholder) is
      mapped through ``page_map`` (placeholder -> resolved slide ID).
    - Every other ``objectId`` / ``connectedObjectId`` gets ``suffix`` so a
      rebuild into an existing deck never collides with old elements.
    """
    def walk(node: Any) -> Any:
        if isinstance(node, dict):
            out = {}
            for k, v in node.items():
                if k == "pageObjectId" and isinstance(v, str):
                    out[k] = page_map.get(v, v)
                elif k in ("objectId", "connectedObjectId") and isinstance(v, str):
                    out[k] = page_map[v] if v in page_map else f"{v}{suffix}"
                else:
                    out[k] = walk(v)
            return out
        if isinstance(node, list):
            return [walk(v) for v in node]
        return node
    return [walk(r) for r in requests]


def filter_requests_for(requests: list[dict[str, Any]], object_ids: set[str]) -> list[dict[str, Any]]:
    """Incremental patch: ``deleteObject`` + recreate only the given elements.

    Keeps every request whose own ``objectId`` is in ``object_ids`` (create,
    style, text). Lets you fix one node/pill without rebuilding the slide.
    """
    keep = [r for r in requests
            if any(isinstance(body, dict) and body.get("objectId") in object_ids for body in r.values())]
    return [{"deleteObject": {"objectId": oid}} for oid in sorted(object_ids)] + keep


# =============================================================================
# Spec normalisation helpers
# =============================================================================
def _s(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _body_text(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        items = [_s(v) for v in value if _s(v)]
        return "\n".join(i if i.startswith(("•", "-", "→")) else f"• {i}" for i in items)
    return _s(value)


def _accent(item: dict[str, Any], idx: int) -> tuple[str, str, str]:
    name = _s(item.get("color")).lower()
    if name in ACCENTS:
        return ACCENTS[name]
    return ACCENTS[ACCENT_ORDER[idx % len(ACCENT_ORDER)]]


def _status(item: dict[str, Any], labels: dict[str, str]) -> Optional[tuple[str, str, str]]:
    raw = _s(item.get("status")).lower().replace(" ", "_")
    if not raw:
        return None
    key = STATUS_ALIASES.get(raw, raw)
    if key not in STATUS_STYLES:
        return None
    label, fill, color = STATUS_STYLES[key]
    label = _s(item.get("status_label")) or _s(labels.get(key)) or label
    return label, fill, color


def _marker(diagram: dict[str, Any]) -> tuple[str, str, int]:
    """Returns (text, target_kind, 0-based index) — target_kind in stage|node|step|entry|''."""
    m = diagram.get("marker")
    if not m:
        return "", "", -1
    if isinstance(m, str):
        m = {"text": m}
    text = _s(m.get("text")) or "WE ARE HERE"
    at = _s(m.get("at")).lower()
    if not at:
        return text, "", -1
    if at == "entry":
        return text, "entry", 0
    kind, _, num = at.partition(":")
    try:
        return text, kind, int(num) - 1
    except ValueError:
        return text, kind, -1


def infer_layout(diagram: dict[str, Any], hint: str = "") -> str:
    layout = _s(diagram.get("layout") or diagram.get("type")).lower() or hint
    if layout in LAYOUTS:
        return layout
    if diagram.get("steps"):
        return "funnel"
    if diagram.get("cycle"):
        return "cycle"
    return "timeline"


def _pill_width(text: str, size: float = SZ_PILL, max_w: float = 240.0) -> float:
    # Bold uppercase-heavy text runs wider than the body-text heuristic.
    return min(max_w, max(84.0, len(text) * size * PILL_CHAR_W + 16))


# =============================================================================
# Components
# =============================================================================
def _marker_pill(c: RawCanvas, text: str, x: float, y: float, max_w: float = 240.0,
                 center_on: Optional[float] = None) -> None:
    w = _pill_width(text, max_w=max_w)
    if center_on is not None:
        x = center_on - w / 2
    x = max(X0, min(x, X1 - w))
    c.box("here_pill", x, y, w, 20, [(text, SZ_PILL, True, C_WHITE)], align="CENTER", valign="MIDDLE",
          kind="ROUND_RECTANGLE", fill=ACCENTS["red"][0], label="marker pill", single_line=True)


def _note(c: RawCanvas, text: str, x: float, y: float, w: float) -> None:
    if text:
        c.box("note", x, y, w, 16, [(text, SZ_NOTE, False, C_GREY)], align="END",
              label="honesty note", single_line=True)


def _section_label(c: RawCanvas, name: str, text: str, x: float, y: float, w: float,
                   color: str = C_GREY) -> None:
    if text:
        c.box(name, x, y, w, 16, [(text.upper(), SZ_LABEL, True, color)], label=f"{name} label",
              single_line=True)


def _stage_runs(stage: dict[str, Any], i: int, w: float) -> list[Run]:
    _accent_fill, accent_text, _tint = _accent(stage, i)
    title_size = SZ_CARD_TITLE if w >= 112 else 12.0
    runs: list[Run] = []
    for txt, size, bold, color in (
        (_s(stage.get("kicker")), SZ_KICKER, True, accent_text),
        (_s(stage.get("title")), title_size, True, C_DARK),
        (_s(stage.get("lead")), SZ_LEAD, True, C_DARK),
        (_body_text(stage.get("body") or stage.get("bullets")), SZ_BODY, False, C_GREY),
    ):
        if txt:
            runs.append((txt + "\n", size, bold, color))
    return runs


def _card_height(runs: list[Run], w: float, has_chip: bool, spacing: float = 105,
                 space_below: float = 5) -> float:
    """Card height that fits its text (+ chip), so short content doesn't float in empty cards."""
    need = _runs_required_height(runs, w - 8, spacing, space_below) * 1.1
    return need + 10 + (34.0 if has_chip else 6.0) + 8


def _stage_card(c: RawCanvas, i: int, stage: dict[str, Any], x: float, y: float, w: float, h: float,
                labels: dict[str, str], highlight: bool = False) -> None:
    accent, accent_text, _tint = _accent(stage, i)
    n = i + 1
    c.shape(f"card{n}", "RECTANGLE", x, y, w, h, fill=C_WHITE,
            outline=accent_text if highlight else C_RULE, weight=1.5 if highlight else 0.75)
    c.shape(f"card{n}_bar", "RECTANGLE", x, y, w, 5, fill=accent)
    status = _status(stage, labels)
    chip_h = 34.0 if status else 6.0
    runs = _stage_runs(stage, i, w)
    c.box(f"card{n}_txt", x + 4, y + 10, w - 8, h - 10 - chip_h, runs, spacing=105, space_below=5,
          label=f"stage {n} card")
    if status:
        label, fill, color = status
        c.box(f"card{n}_chip", x + 8, y + h - 28, w - 16, 20, [(label, SZ_CHIP, True, color)],
              align="CENTER", valign="MIDDLE", kind="ROUND_RECTANGLE", fill=fill,
              label=f"stage {n} status chip", single_line=True)


def _arrow(c: RawCanvas, name: str, x_from: float, x_to: float, y: float, color: str = C_GREY) -> None:
    if x_to - x_from > 2:
        c.line(name, x_from, y, x_to - x_from, 0, color=color)


# =============================================================================
# Layouts
# =============================================================================
def _layout_timeline(c: RawCanvas, d: dict[str, Any], labels: dict[str, str]) -> None:
    stages = [s for s in (d.get("stages") or []) if isinstance(s, dict)]
    n = max(1, len(stages))
    gap = 22.0
    w = (X1 - X0 - (n - 1) * gap) / n
    need = max([_card_height(_stage_runs(st, i, w), w, bool(_status(st, labels)))
                for i, st in enumerate(stages)] or [0.0])
    h = min(228.0, max(150.0, need))
    y = 124.0  # top-anchored under the header; slack goes to the bottom, not between header and content
    m_text, m_kind, m_idx = _marker(d)
    if not (m_text and m_kind == "stage" and m_idx == 0):
        _section_label(c, "lbl_stages", _s(d.get("label")), X0, y - 20, 300)
    for i, st in enumerate(stages):
        x = X0 + i * (w + gap)
        _stage_card(c, i, st, x, y, w, h, labels, highlight=(m_kind == "stage" and m_idx == i))
        if i:
            _arrow(c, f"arr_s{i}", x - gap, x, y + h / 2)
    if m_text and m_kind == "stage" and 0 <= m_idx < n:
        _marker_pill(c, m_text, 0, y - 24, max_w=max(w + gap, 140), center_on=X0 + m_idx * (w + gap) + w / 2)
    elif m_text and not m_kind:
        _marker_pill(c, m_text, X1, y - 24)
    _note(c, _s(d.get("note")), X0, min(356.0, y + h + 6), X1 - X0)


def _layout_cycle(c: RawCanvas, d: dict[str, Any], labels: dict[str, str]) -> None:
    stages = [s for s in (d.get("stages") or []) if isinstance(s, dict)][:MAX_STAGES["cycle"]]
    cyc = d.get("cycle") if isinstance(d.get("cycle"), dict) else {}
    nodes = [n for n in (cyc.get("nodes") or []) if isinstance(n, dict)][:4]
    m_text, m_kind, m_idx = _marker(d)

    card_w, card_gap = 120.0, 14.0
    panel_x = X0 + len(stages) * (card_w + card_gap)
    panel_w = X1 - panel_x
    narrow = panel_w < 460

    # Foundation stages on the left, vertically centred on the loop.
    if stages:
        _section_label(c, "lbl_stages", _s(d.get("label")), X0, 104, panel_x - X0 - card_gap)
    for i, st in enumerate(stages):
        x = X0 + i * (card_w + card_gap)
        _stage_card(c, i, st, x, 124, card_w, 232, labels, highlight=(m_kind == "stage" and m_idx == i))
        if i:
            _arrow(c, f"arr_s{i}", x - card_gap, x, MID_Y)

    c.shape("loop_bg", "ROUND_RECTANGLE", panel_x, Y0, panel_w, Y1 - Y0, fill=C_PANEL)
    _section_label(c, "lbl_loop", _s(cyc.get("label")), panel_x + 10, 106, panel_w - 20,
                   color=ACCENTS["blue"][1])

    inner_l = panel_x + 8
    inner_r = panel_x + panel_w - 6
    blue, blue_t, _ = ACCENTS["blue"]

    entry = cyc.get("entry") if isinstance(cyc.get("entry"), dict) else None
    feeder = cyc.get("feeder") if isinstance(cyc.get("feeder"), dict) else None
    ew, eh = (80.0 if narrow else 100.0), 64.0
    ex, ey = inner_l, MID_Y - eh / 2
    entry_id = None
    if entry:
        entry_id = c.box("node_entry", ex, ey, ew, eh,
                         [(_s(entry.get("title")) + "\n", 10, True, C_WHITE),
                          (_body_text(entry.get("body")), SZ_NODE_BODY, False, C_WHITE)],
                         align="CENTER", valign="MIDDLE", kind="ROUND_RECTANGLE", fill=blue, space_below=2,
                         label="cycle entry node")
    if entry and feeder:
        fy = 300.0
        c.box("node_feed", ex, fy, ew, 50,
              [(_s(feeder.get("title")) + "\n", SZ_KICKER, True, blue_t),
               (_body_text(feeder.get("body")), SZ_NODE_BODY, False, C_GREY)],
              align="CENTER", valign="MIDDLE", kind="ROUND_RECTANGLE", fill=C_WHITE, outline=blue,
              weight=1.0, dash="DASH", space_below=1, label="cycle feeder node")
        c.line("arr_feed", ex + ew / 2, ey + eh, 0, fy - (ey + eh), color=blue, start="FILL_ARROW", end=None)

    nw, nh = (86.0 if narrow else 112.0), 50.0
    left_edge = (ex + ew + 36) if entry else inner_l + 6
    lcx = left_edge + nw / 2
    rcx = inner_r - nw / 2
    span_cap = 300.0 if narrow else 340.0
    if rcx - lcx > span_cap:
        extra = (rcx - lcx) - span_cap
        lcx += extra / 2
        rcx -= extra / 2
    tcx = (lcx + rcx) / 2
    top_cy, bot_cy = 158.0, 322.0

    if len(nodes) == 3:
        centres = [(lcx, MID_Y + 30), (tcx, top_cy), (rcx, MID_Y + 30)]
    else:
        centres = [(lcx, MID_Y), (tcx, top_cy), (rcx, MID_Y), (tcx, bot_cy)]
    node_ids: list[str] = []
    for i, (node, (cx, cy)) in enumerate(zip(nodes, centres)):
        hl = m_kind == "node" and m_idx == i
        node_ids.append(c.box(
            f"node_{i + 1}", cx - nw / 2, cy - nh / 2, nw, nh,
            [(_s(node.get("title")) + "\n", SZ_NODE_TITLE, True, C_DARK),
             (_body_text(node.get("body")), SZ_NODE_BODY, False, C_GREY)],
            align="CENTER", valign="MIDDLE", kind="ROUND_RECTANGLE", fill=C_WHITE,
            outline=ACCENTS["red"][0] if hl else blue, weight=2.0 if hl else 1.25, space_below=1,
            label=f"cycle node {i + 1}"))

    if entry_id and node_ids:
        _arrow(c, "arr_entry", ex + ew, lcx - nw / 2, MID_Y if len(nodes) != 3 else MID_Y, color=blue)
    if stages:
        target_x = ex if entry else lcx - nw / 2
        _arrow(c, "arr_s_loop", X0 + len(stages) * (card_w + card_gap) - card_gap, target_x, MID_Y)

    # Curved clockwise connectors glued to connection sites.
    if len(node_ids) == 4:
        sites = [(0, SITE_TOP, 1, SITE_LEFT), (1, SITE_RIGHT, 2, SITE_TOP),
                 (2, SITE_BOTTOM, 3, SITE_RIGHT), (3, SITE_LEFT, 0, SITE_BOTTOM)]
    elif len(node_ids) == 3:
        sites = [(0, SITE_TOP, 1, SITE_LEFT), (1, SITE_RIGHT, 2, SITE_TOP), (2, SITE_BOTTOM, 0, SITE_BOTTOM)]
    else:
        sites = []
    for a, sa, b, sb in sites:
        (ax, ay), (bx, by) = centres[a], centres[b]
        x, y = min(ax, bx), min(ay, by)
        c.line(f"loop_{a + 1}{b + 1}", x, y, abs(bx - ax), abs(by - ay), color=blue_t, weight=1.5,
               category="CURVED", conn=((node_ids[a], sa), (node_ids[b], sb)))

    centre = cyc.get("center") or cyc.get("centre")
    if centre and len(node_ids) == 4:
        if isinstance(centre, str):
            centre = {"text": centre}
        icon = _s(centre.get("icon")) or "↻"
        c.box("loop_center", tcx - 46, MID_Y - 29, 92, 58,
              [(icon + "\n", 18, True, blue), (_s(centre.get("text")), SZ_NODE_BODY, False, C_GREY)],
              align="CENTER", valign="MIDDLE", spacing=95, label="cycle centre caption")

    if m_text:
        if m_kind == "entry" and entry:
            # Stop short of the left node's centre: the curved connector leaves from its top.
            limit = lcx - ex - 6
            _marker_pill(c, m_text, ex, ey - 24, max_w=max(limit, 90))
        elif m_kind == "node" and 0 <= m_idx < len(centres):
            cx, cy = centres[m_idx]
            py = cy + nh / 2 + 4 if m_idx == 1 else cy - nh / 2 - 22
            _marker_pill(c, m_text, 0, py, max_w=160, center_on=cx)
        elif m_kind == "stage" and 0 <= m_idx < len(stages):
            _marker_pill(c, m_text, 0, 100, max_w=card_w + card_gap,
                         center_on=X0 + m_idx * (card_w + card_gap) + card_w / 2)
    _note(c, _s(d.get("note")), panel_x + 10, 354, panel_w - 20)


def _funnel_runs(st: dict[str, Any], i: int) -> list[Run]:
    _fill, accent_text, _tint = _accent(st, i)
    runs: list[Run] = []
    title = _s(st.get("title")) if st.get("label") else ""
    for txt, size, bold, color in (
        (title, 11.0, True, C_DARK),
        (_s(st.get("lead")), SZ_LEAD, True, accent_text),
        (_body_text(st.get("body") or st.get("bullets")), SZ_BODY, False, C_GREY),
    ):
        if txt:
            runs.append((txt + "\n", size, bold, color))
    return runs


def _layout_funnel(c: RawCanvas, d: dict[str, Any], labels: dict[str, str]) -> None:
    steps = [s for s in (d.get("steps") or []) if isinstance(s, dict)]
    n = max(1, len(steps))
    active = d.get("active")
    try:
        active_idx = int(active) - 1 if active is not None else -1
    except (TypeError, ValueError):
        active_idx = -1
    m_text, m_kind, m_idx = _marker(d)

    overlap = 8.0
    chev_w = (X1 - X0 + (n - 1) * overlap) / n
    chev_h = 28.0
    gap = 10.0
    card_w = (X1 - X0 - (n - 1) * gap) / n
    need = max([_card_height(_funnel_runs(st, i), card_w, bool(_status(st, labels)), space_below=4)
                for i, st in enumerate(steps)] or [0.0])
    card_h = min(190.0, max(110.0, need))
    chev_y = 124.0
    card_y = chev_y + chev_h + 10
    if not (m_text and m_kind == "step"):
        _section_label(c, "lbl_steps", _s(d.get("label")), X0, chev_y - 20, 300)

    for i, st in enumerate(steps):
        accent, accent_text, tint = _accent(st, i)
        is_active = active_idx < 0 or i == active_idx
        fill, txt_color = (accent, C_WHITE) if is_active else (tint, accent_text)
        if is_active and accent == ACCENTS["yellow"][0]:
            txt_color = C_DARK  # white on yellow fails contrast
        x = X0 + i * (chev_w - overlap)
        label = _s(st.get("label") or st.get("title")).upper()
        c.box(f"chev{i + 1}", x, chev_y, chev_w, chev_h, [(label, 9, True, txt_color)], align="CENTER",
              valign="MIDDLE", kind="HOME_PLATE" if i == 0 else "CHEVRON", fill=fill,
              label=f"funnel step {i + 1} chevron", single_line=True)

        cx = X0 + i * (card_w + gap)
        hl = i == active_idx
        c.shape(f"card{i + 1}", "RECTANGLE", cx, card_y, card_w, card_h, fill=C_WHITE,
                outline=accent_text if hl else C_RULE, weight=1.5 if hl else 0.75)
        c.shape(f"card{i + 1}_bar", "RECTANGLE", cx, card_y, card_w, 4, fill=accent)
        status = _status(st, labels)
        chip_h = 34.0 if status else 6.0
        runs = _funnel_runs(st, i)
        c.box(f"card{i + 1}_txt", cx + 4, card_y + 10, card_w - 8, card_h - 10 - chip_h, runs,
              spacing=105, space_below=4, label=f"funnel step {i + 1} card")
        if status:
            s_label, s_fill, s_color = status
            c.box(f"card{i + 1}_chip", cx + 8, card_y + card_h - 28, card_w - 16, 20,
                  [(s_label, SZ_CHIP, True, s_color)], align="CENTER", valign="MIDDLE",
                  kind="ROUND_RECTANGLE", fill=s_fill, label=f"funnel step {i + 1} status chip",
                  single_line=True)

    if m_text and m_kind == "step" and 0 <= m_idx < n:
        _marker_pill(c, m_text, 0, chev_y - 24, max_w=max(chev_w, 140),
                     center_on=X0 + m_idx * (chev_w - overlap) + chev_w / 2)
    _note(c, _s(d.get("note")), X0, min(356.0, card_y + card_h + 6), X1 - X0)


_LAYOUT_FN = {"timeline": _layout_timeline, "cycle": _layout_cycle, "funnel": _layout_funnel}


def build_diagram_canvas(page_id: str, diagram: dict[str, Any], prefix: str = "dg01",
                         layout_hint: str = "") -> RawCanvas:
    """Lays out a diagram and returns the populated canvas (requests + text boxes)."""
    d = diagram if isinstance(diagram, dict) else {}
    canvas = RawCanvas(page_id, prefix)
    labels = d.get("status_labels") if isinstance(d.get("status_labels"), dict) else {}
    _LAYOUT_FN[infer_layout(d, layout_hint)](canvas, d, labels)
    return canvas


# =============================================================================
# Validation (structure + fit) — used by spec.validator
# =============================================================================
def _runs_required_height(runs: list[Run], width: float, spacing: float, space_below: float) -> float:
    usable = max(10.0, width - 2 * TEXTBOX_INNER_PADDING)
    total = 0.0
    for text, size, _bold, _color in runs:
        cpl = max(1, math.floor(usable / (size * CHAR_WIDTH_PROPORTIONAL)))
        paragraphs = text.rstrip("\n").split("\n")
        for p in paragraphs:
            lines = max(1, math.ceil(len(p) / cpl))
            total += lines * size * LINE_HEIGHT_FACTOR * (spacing / 100.0) + space_below
    return total


def fit_issues(canvas: RawCanvas) -> list[str]:
    out = []
    for tb in canvas.text_boxes:
        runs = [r for r in tb["runs"] if r[0].strip()]
        if not runs:
            continue
        if tb["single_line"]:
            text, size = runs[0][0], runs[0][1]
            cap = max(1, math.floor((tb["w"] - 14) / (size * PILL_CHAR_W)))
            if len(text) > cap:
                out.append(f"{tb['label']} '{text[:40]}' will wrap ({len(text)} chars, ~{cap} fit on one line)")
            continue
        need = _runs_required_height(runs, tb["w"], tb["spacing"], tb["space_below"])
        if need > tb["h"] * 1.08 + 4:
            out.append(f"{tb['label']} overflows (needs ~{need:.0f}pt, box {tb['h']:.0f}pt) — shorten text")
    return out


def validate_diagram(diagram: Any, layout_hint: str = "") -> tuple[list[str], list[str]]:
    """Returns (errors, warnings) for a flow_diagram `diagram:` block."""
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(diagram, dict) or not diagram:
        return ["requires a `diagram:` block (layout + stages/cycle/steps)"], []
    layout = infer_layout(diagram, layout_hint)
    raw_layout = _s(diagram.get("layout") or diagram.get("type")).lower()
    if raw_layout and raw_layout not in LAYOUTS:
        errors.append(f"diagram.layout must be one of {list(LAYOUTS)}, got '{raw_layout}'")
    stages = diagram.get("stages") or []
    if layout == "timeline":
        if not 2 <= len(stages) <= MAX_STAGES["timeline"]:
            errors.append(f"timeline needs 2-{MAX_STAGES['timeline']} stages, got {len(stages)}")
    elif layout == "cycle":
        cyc = diagram.get("cycle")
        if not isinstance(cyc, dict):
            errors.append("cycle layout requires `cycle: {nodes: [...]}`")
        else:
            nodes = cyc.get("nodes") or []
            if len(nodes) not in (3, 4):
                errors.append(f"cycle needs 3 or 4 nodes, got {len(nodes)}")
            if cyc.get("feeder") and not cyc.get("entry"):
                warnings.append("cycle.feeder is drawn only when cycle.entry exists")
        if len(stages) > MAX_STAGES["cycle"]:
            errors.append(f"cycle layout fits at most {MAX_STAGES['cycle']} stages on the left, got {len(stages)}")
    elif layout == "funnel":
        steps = diagram.get("steps") or []
        if not 3 <= len(steps) <= 6:
            errors.append(f"funnel needs 3-6 steps, got {len(steps)}")

    m_text, m_kind, m_idx = _marker(diagram)
    if m_text and m_kind and m_kind not in ("stage", "node", "step", "entry"):
        errors.append(f"marker.at must be entry | stage:N | node:N | step:N, got '{m_kind}'")
    if m_text and not m_kind:
        warnings.append("marker has no `at:` (entry | stage:N | node:N | step:N); it will float top-right")

    def walk(node: Any, path: str) -> None:
        if isinstance(node, str):
            bad = non_bmp_chars(node)
            if bad:
                warnings.append(f"diagram.{path} contains emoji/non-BMP chars {''.join(bad)} — they are "
                                "stripped (render unreliably); use BMP symbols like ✓ ● → ↻")
        elif isinstance(node, dict):
            for k, v in node.items():
                walk(v, f"{path}.{k}" if path else str(k))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")
    walk(diagram, "")

    if not errors:
        try:
            canvas = build_diagram_canvas("PAGE_CHECK", diagram, "chk01", layout_hint)
            warnings.extend(fit_issues(canvas))
        except Exception as e:  # pylint: disable=broad-except
            errors.append(f"diagram layout failed: {e}")
    return errors, warnings


# =============================================================================
# Archetype generator
# =============================================================================
def generate_flow_diagram(
    slide_id: str,
    title: str,
    subtitle: str,
    kicker: str,
    diagram: dict[str, Any],
    speaker_notes: str = "",
    layout_hint: str = "",
    header_ops: Optional[list[dict[str, Any]]] = None,
    slide_idx: str = "01",
) -> list[dict[str, Any]]:
    """Generates batch ops for Archetype 11 (flow_diagram).

    Emits the slide, background, standard header and notes as normal batch
    ops, plus one ``_raw-requests`` marker carrying the diagram body.
    """
    ops: list[dict[str, Any]] = [
        {"op": "add-slide", "layout": "BLANK", "id": slide_id},
        {"op": "set-background", "slide": slide_id, "color": "#F8F9FA"},
    ]
    ops.extend(header_ops or [])
    canvas = build_diagram_canvas(slide_id, diagram or {}, prefix=f"dg{slide_idx}", layout_hint=layout_hint)
    ops.append({"op": "_raw-requests", "slide": slide_id, "requests": canvas.requests})
    if speaker_notes:
        ops.append({"op": "set-notes", "slide": slide_id, "text": speaker_notes})
    return ops
