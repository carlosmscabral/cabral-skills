# The stepped slideshow

Use this when the drawing will be presented, projected, or left on a screen
people walk past. One drawing, many screens: each step lights its own arrow,
dims everything else, and zooms the frame onto what it lit.

Zoom improves focus, but does not guarantee phone readability. Measure the
rendered font size, and use smaller detail views or the component picker to
provide readable explanations when a long edge still spans most of the drawing.

## A slide is a number, a title and one line

```js
{
  n: "4", tone: "yellow", title: "Reads the face",
  line: "One call pulls six traits out of the three photographs.",
  facts: [["Model", "gemini-3-flash"], ["Calls", "1"], ["Time", "6 s"]],
  edges: ["e4"], units: ["api", "vision"]
}
```

Hold the line to about 25 words. The page exists to put the drawing first, and
the way it fails is a slide quietly growing back into a paragraph. If a
component needs more than that, the extra belongs in its hover text, not on
the slide.

## Open and close on the whole architecture

Two slides carry no step number and light nothing, so the drawing shows
complete and undimmed. They are not filler.

The **first** one is the reason the rest works. A reader who sees the whole
shape before anything moves can place each step inside it; a slideshow that
opens already zoomed into one arrow shows them parts and never the system. Give
that slide the thesis in one sentence, not a list of contents.

The **last** one shows the same picture again, now that they know what is in
it. That is where the measured numbers belong, or the one claim you want them
to leave with.

Journey slides light one numbered step. Security, failure or operations slides
may light several related edges. Use optional `notes` for rationale and evidence.
Zoom does not guarantee phone readability: measure actual rendered font size and
provide smaller detail views or accessible explanations when necessary.

## The frame computes itself

A slide names what it lights. The zoom comes from that list, so adding a step
costs one array entry and no coordinates.

```js
const VW = 1025, VH = 745;          // the viewBox

function focusBox(slide) {
  let x1 = Infinity, y1 = Infinity, x2 = -Infinity, y2 = -Infinity;
  const grow = (ax, ay, bx, by) => {
    x1 = Math.min(x1, ax); y1 = Math.min(y1, ay);
    x2 = Math.max(x2, bx); y2 = Math.max(y2, by);
  };
  for (const id of slide.units) {
    const u = byId[id];
    if (u) grow(u.x, u.y, u.x + u.w, u.y + u.h);
  }
  for (const id of slide.edges) {
    for (const [px, py] of edgeById[id].pts) grow(px, py, px, py);
  }
  if (x1 === Infinity) return { x: 0, y: 0, w: VW, h: VH };   // light nothing, show all
  const pad = 46;
  return { x: x1 - pad, y: y1 - pad, w: x2 - x1 + pad * 2, h: y2 - y1 + pad * 2 };
}

function frameStage(slide) {
  const f = focusBox(slide);
  const s = Math.max(1, Math.min(VW / f.w, VH / f.h, 2.3));    // never below 1, never above 2.3
  const cx = f.x + f.w / 2, cy = f.y + f.h / 2;
  let tx = VW / 2 - s * cx, ty = VH / 2 - s * cy;
  tx = Math.min(0, Math.max(VW * (1 - s), tx));                // keep the drawing's edges inside
  ty = Math.min(0, Math.max(VH * (1 - s), ty));
  stage.setAttribute('transform', `translate(${tx} ${ty}) scale(${s})`);
}
```

Three details that matter:

- **Transform a group, not the `viewBox`.** CSS cannot transition a `viewBox`
  attribute, and it transitions a `transform` on a `<g>` for free. Wrap all
  three layers in one `<g id="stage">`.
- **Cap the scale at about 2.3.** Past that the stroke widths scale into
  something coarse and the drawing stops looking drafted.
- **Clamp the translate.** Without the clamp, a step near an edge frames empty
  space beside the drawing.

## Dimming

```css
.unit, .wirepart { transition: opacity .4s; }
.dim { opacity: .14; }
```

Fourteen percent is the number that reads as "still there, not the point". At
30 percent the dimmed components still compete; at 5 percent the drawing looks
broken.

Keep the dimmed components hoverable and un-dim on hover. Someone will always
want to know what the grey box behind the active one is.

## Fade the cropped edges

When the frame zooms in, the drawing runs off the sheet and the cut lands
mid-word. A hard cut reads as broken text; a fade reads as "there is more
outside the frame".

```css
.sheet::after {
  content: "";
  position: absolute;
  inset: 14px;               /* match the sheet's padding */
  pointer-events: none;
  opacity: 0;
  transition: opacity .35s;
  background:
    linear-gradient(to right,  #FFF, rgba(255,255,255,0) 46px),
    linear-gradient(to left,   #FFF, rgba(255,255,255,0) 46px),
    linear-gradient(to bottom, #FFF, rgba(255,255,255,0) 32px),
    linear-gradient(to top,    #FFF, rgba(255,255,255,0) 32px);
}
.sheet.zoomed::after { opacity: 1; }
```

Toggle `zoomed` only while the scale is above 1. At full view there is nothing
to fade, and the gradient would wash out the drawing's own outer labels.

## Getting around

Give people every way in, because you do not know which one they will reach
for:

```js
addEventListener('keydown', (e) => {
  if (e.key === 'ArrowRight' || e.key === ' ') go(at + 1);
  else if (e.key === 'ArrowLeft') go(at - 1);
  else if (e.key === 'Home') go(0);
  else if (e.key === 'End') go(SLIDES.length - 1);
});
```

Plus a step rail of numbered buttons, previous and next buttons, and a swipe:

```js
let downX = null;
stage.addEventListener('pointerdown', (e) => { downX = e.clientX; });
stage.addEventListener('pointerup', (e) => {
  if (downX !== null && Math.abs(e.clientX - downX) > 55) go(at + (e.clientX < downX ? 1 : -1));
  downX = null;
});
```

Make sure the whole rail fits at phone width. Thirteen steps at 19 px each
with 3 px gaps is 271 px, which fits beside two 30 px arrows on a 390 px
screen. If it does not fit, the rail scrolls and people stop believing they
have seen every step.

## For an unattended screen

An attract loop, off by default, nine seconds a slide:

```js
let timer = null;
playBtn.addEventListener('click', () => {
  if (timer) { clearInterval(timer); timer = null; return; }
  timer = setInterval(() => go(at + 1), 9000);
  go(at + 1);
});
```

Stop it on any manual navigation. Someone who presses an arrow key has taken
over, and a slide moving under them is the fastest way to lose them.

## Sizing the shell

```css
html, body { height: 100%; }
body { overflow: hidden; }
.shell { height: 100%; display: flex; flex-direction: column; }
.screen { flex: 1; min-height: 0; display: grid; grid-template-columns: minmax(260px, 24vw) 1fr; }
```

Use `height: 100%` rather than `100vh`: it respects the safe-area padding a
host may add, and on a phone browser it does not fight the collapsing address
bar. Every flex and grid child that contains the drawing needs `min-height: 0`
or it refuses to shrink.

Below 900 px, stack the caption above the drawing:

```css
@media (max-width: 900px), (max-height: 520px) {
  .screen { grid-template-columns: 1fr; grid-template-rows: auto minmax(0, 1fr); }
}
```

The short-viewport clause matters. A laptop in presentation mode at 1280 x 500
needs the stacked layout as much as a phone does.
