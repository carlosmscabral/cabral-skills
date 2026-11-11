# Layout rules

Read this before you place the first coordinate. Every rule here exists
because a real diagram broke without it.

## Why the coordinates are absolute

You place every box by hand, in the SVG's own units. No layout engine, no
auto-routing, no force-directed anything.

Automatic placement fails on this kind of drawing for one reason: the
information is in the grouping. A reader learns "these three run in the public
service" from the tinted box around them, and an engine that is free to move
boxes will break that grouping to shorten an edge. You are drawing a claim
about the system, not a graph.

The cost is that you own every collision. The audit at the bottom of this file
is how you pay it.

## The painting order

Three layers, in this order:

```
frames   the cloud boundary, the group rectangles, their titles
wires    connectors, arrowheads, labels, numbered discs
units    the boxes and the product cards, with their text
```

**Units paint last, so a card's fill covers anything under it.** A connector
label that runs under a card is not dimmed, it is gone. This is the most
common defect in these drawings and the audit's second check exists for it.

Groups paint first, so a wire crossing a tinted group reads correctly.

## Columns and corridors

Lay the drawing out in columns:

```
left        actors, outside the cloud boundary
middle      the services the request enters
right       the things those services call: models, datastores, telemetry
```

The vertical gap between two columns is a **corridor**, and that corridor is
where every connector, label and numbered disc has to fit. Size it from what
it must hold, not from what looks balanced:

| Element | Width it needs |
| :--- | :--- |
| A numbered disc, radius 9 | 18 px plus clearance |
| A label, 10 px monospace | about 6 px per character |
| An arrowhead | 7 px |

A corridor of 76 px cannot hold a disc and a 13-character label. One of 120 px
can. When in doubt, widen the corridor rather than shorten the words.

## Lanes

Inside a corridor, connectors run in **lanes**: vertical tracks at fixed x
positions, 12 px apart. Assign one lane per connector and write the lane
numbers down.

**Two connectors may share a lane only when their vertical spans do not
overlap.** An arrow going up from y 320 to y 124 and an arrow going down from
y 352 to y 660 can both use the same lane, because they never occupy the same
pixel. Two arrows both crossing y 400 cannot.

Crossings between a lane and a horizontal segment are fine and normal. Do not
contort a route to avoid one; real reference architectures have several.

## Labels

Give every label an explicit position and anchor. Computed placement
("above the midpoint", "left of the first point") collides with something in
every dense drawing, and then you are debugging a placement function instead
of moving a number.

```js
{ id: "e4", n: "4", from: "api", to: "model",
  pts: [[524, 322], [598, 322], [598, 124], [620, 124]],
  disc: [598, 223],
  label: "1 call", lx: 614, ly: 117, anchor: "end" }
```

Three rules for the text itself:

1. **Punch it out of the lines.** A label crossing a connector is unreadable
   without a halo:

   ```css
   .wire-label {
     paint-order: stroke;
     stroke: #FFFFFF;       /* the sheet colour */
     stroke-width: 3.5px;
     stroke-linejoin: round;
   }
   ```

   The halo adds 3.5 px on every side. Count it when you check clearance.

2. **Never repeat the card.** If the target card's subtitle already reads
   `gemini-3-flash · 6 calls`, the arrow label "6 calls" is noise. Delete it.
   Most connectors in a good drawing carry no label at all.

3. **Keep the disc off the label.** On a short straight run the midpoint is
   where both want to sit. Put the disc near the source and the label near the
   target, and check the gap.

## Groups

```
fill    a very light tint of the group's hue
stroke  a mid tint of the same hue, 1.2 px
radius  8
title   12.5 px, 500 weight, 14 px in from the left, 21 px down from the top
```

A dashed stroke means the group is not part of the running system: build
pipelines, container registries, CI. Readers pick this up without a legend.

Cards sit at least 14 px inside their group on every side.

## The audit

First run `node scripts/validate-data.cjs data.js` on trusted diagram data.
It checks IDs, references, orthogonal routes and whether every connector endpoint
touches the component it names. Visual proximity is not enough.

Open the rendered page and run this in the browser console. It reports text
that escapes its own box, labels a card paints over, marks that collide, and
ids a slide names that the drawing does not have.

```js
const svg = document.querySelector('svg');
const box = (e) => { const b = e.getBBox(); return { x: b.x, y: b.y, x2: b.x + b.width, y2: b.y + b.height }; };
const hit = (a, b) => a.x < b.x2 && b.x < a.x2 && a.y < b.y2 && b.y < a.y2;
const units = [...svg.querySelectorAll('.unit')].map((g) => ({ id: g.id, b: box(g.querySelector('rect')) }));
const out = [];

// 1. text wider than the box it belongs to
for (const g of svg.querySelectorAll('.unit')) {
  const r = box(g.querySelector('rect'));
  for (const t of g.querySelectorAll('text')) {
    const b = box(t);
    if (b.x < r.x + 3 || b.x2 > r.x2 - 3 || b.y < r.y + 2 || b.y2 > r.y2 - 2) {
      out.push(['escapes', g.id, t.textContent]);
    }
  }
}

// 2. connector labels a card will paint over
for (const t of svg.querySelectorAll('.wire-label')) {
  for (const u of units) if (hit(box(t), u.b)) out.push(['covered', t.textContent, u.id]);
}

// 3. labels and numbered discs landing on each other
const marks = [...svg.querySelectorAll('.wire-label, .disc-n, .grp-title')].map((e) => ({ t: e.textContent, b: box(e) }));
for (let i = 0; i < marks.length; i++) {
  for (let j = i + 1; j < marks.length; j++) {
    if (hit(marks[i].b, marks[j].b)) out.push(['collide', marks[i].t, marks[j].t]);
  }
}

// 4. slides pointing at something the drawing does not have
if (typeof SLIDES !== 'undefined') {
  const drawn = new Set([...OUTSIDE, ...CARDS].map((u) => u.id));
  const wired = new Set(EDGES.map((e) => e.id));
  for (const s of SLIDES) {
    for (const id of s.units) if (!drawn.has(id)) out.push(['no such unit', s.title, id]);
    for (const id of s.edges) if (!wired.has(id)) out.push(['no such edge', s.title, id]);
  }
}

out;
```

**An empty array is the passing result.** Run it after every edit to the data.

The fourth check earns its place because its failure is silent. A slide that
names an id nothing draws dims the whole drawing and lights none of it, which
reads as a broken page rather than as a typo in one string.

A second check, for the page around the drawing, at each width you care about:

```js
const vw = document.documentElement.clientWidth;
[...document.querySelectorAll('body *')]
  .filter((el) => !el.ownerSVGElement && el.tagName !== 'svg')
  .filter((el) => { const r = el.getBoundingClientRect(); return r.width && (r.right > vw + 0.5 || r.left < -0.5); })
  .map((el) => el.className + ' | ' + el.textContent.trim().slice(0, 24));
```

To test a narrow width without resizing the window, load the page in an
iframe of that width: media queries follow the iframe's viewport.

```js
const f = document.createElement('iframe');
f.style.cssText = 'position:fixed;left:0;top:0;width:390px;height:780px;border:0;z-index:9999';
f.src = location.href;
document.body.appendChild(f);
// then run the check inside f.contentDocument / f.contentWindow
```

## Sizing and responsiveness

Give the SVG a `viewBox` and let it scale:

```html
<svg viewBox="0 0 1025 745" preserveAspectRatio="xMidYMid meet"
     style="width:100%;height:100%"></svg>
```

Set the `viewBox` from the content's real extent plus a small margin. Measure
it; do not guess.

A full drawing is unreadable below about 900 px. You have two ways out, and
the first is better:

1. **Zoom to the active step**, which is what `slideshow.md` describes. The
   same drawing, framed on one arrow, is legible at 390 px.
2. **A stacked list** of the same components, shown instead of the drawing
   below the breakpoint. More code, and it duplicates the content.

Never let the drawing shrink until its 10 px labels are unreadable. That is
the failure mode of most architecture pages.

## Colour

Use the provider's own hues for the groups, at two tints each: a very light
fill and a mid-tone border. Reserve the saturated versions for the lit state
of a step.

Keep a separate accent for the page chrome if that chrome is dark. A colour
that reads on white does not read on near-black, so carry both values and pick
per surface.
