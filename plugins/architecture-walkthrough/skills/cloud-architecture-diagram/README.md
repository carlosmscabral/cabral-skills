# Cloud Architecture Diagram

## Updated visual workflow

The renderer defaults to a clean light theme. Set `DIAGRAM.theme: "dark"` for
booth chrome or `DIAGRAM.mode: "diagram"` for a standalone overview. Optional
`notice`, `legend`, slide `notes` and component `why` keep evidence and explanations
available without crowding the drawing. Print produces an undimmed overview.

For Google Slides/PPTX, follow `references/slides-and-export.md` with a presentation
tool; HTML is not an editable deck. New references cover visual hierarchy and
Google Cloud boundary, identity and asynchronous-flow semantics.

Validate trusted data with `node scripts/validate-data.cjs assets/example-data.js`,
then run the geometry audit and visually inspect every slide at delivery sizes.
The bundled example is illustrative, not evidence of a production deployment.

An Agy skill for drawing a deployed system the way a cloud vendor's reference
architecture draws it, and shipping the drawing as one self-contained,
interactive HTML page.

Google Cloud product icons, a cloud boundary with actors outside it, tinted
environment groups, orthogonal connectors, and a numbered path that follows
one request from end to end. Hover any component to read what it does. Step
through it slide by slide if it is going on a screen.

## What it produces

One `.html` file with no build step, no imports, and no runtime dependency
beyond a font stylesheet. It has to render from a `file://` URL, from an email
attachment, and on a conference network that blocks every CDN, so everything
is inline.

## Why not Mermaid

Mermaid, Graphviz and every other layout engine place the nodes for you, and
automatic placement is what makes a diagram look generated.

The information in this kind of drawing is in the grouping. A reader learns
"these three run inside the public service" from the tinted box drawn around
them, and an engine free to move boxes will break that grouping to shorten an
edge. You are drawing a claim about a system, not rendering a graph.

The price is that you own every collision. The skill pays it with a
measurement script instead of with your eyes.

## When does it activate?

| Trigger | Example |
| :--- | :--- |
| Architecture diagram | "Draw the architecture of this service" |
| A component map | "Show me how this app is wired on GCP" |
| In Portuguese | "Faz um desenho de arquitetura disso" |
| A reference image | Sharing a vendor reference architecture and saying "like this" |
| Explaining a deployment | "I need a page that explains how the demo works" |

## How it works with you

It draws **with** you, using these checkpoints and preserving existing approvals:

1. **Where does this live?** A page you scroll, a screen you step through, or
   an image in a deck. The answer decides whether it builds a slideshow, and
   that is expensive to reverse later.
2. **Is this the inventory, and is this the request path?** It reads the
   repository or asks, writes both back as a plain list, and waits. Getting the
   inventory wrong costs a redraw; getting it right costs one message.
3. **The audit before the screenshot.** It draws, measures, fixes and measures
   again, and only shows you the result once the audit is clean.
4. **What could it not verify?** It names its own uncertainty instead of hiding
   it, because you are the one who knows which guess is wrong.

After that, changes are changes to the data. A new component is one entry; a
new step is one entry and no coordinates.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/duboc/agy-skills/main/scripts/install.sh | bash -s -- cloud-architecture-diagram
```

Or copy `skills/cloud-architecture-diagram/` to `~/.gemini/config/skills/`.

## Use it by hand

The skill drives this for you, but the pieces work on their own.

```bash
cd ~/.gemini/config/skills/cloud-architecture-diagram

# 1. pull the product icons you need
./scripts/fetch-gcp-icons.sh --list | less
./scripts/fetch-gcp-icons.sh cloud-run firestore cloud-storage vertexai > icons.js

# 2. write the boxes, groups, connectors and steps
cp assets/example-data.js my-diagram.js
$EDITOR my-diagram.js

# 3. splice them into the renderer
./scripts/build-diagram.sh icons.js my-diagram.js > architecture.html
```

Open `architecture.html`, then paste the audit from
`references/layout-rules.md` into the console. An empty array is the passing
result. Rebuild and re-run after every edit to the data.

`assets/example-data.js` is a working diagram, not a stub: a photo-upload API
on Cloud Run that calls a model, stores the result and reports what it did.
Build it as-is to see the shape before you change anything.

## What is in here

| File | Holds |
| :--- | :--- |
| `SKILL.md` | The instructions Agy follows. |
| `references/layout-rules.md` | Geometry, corridors, lanes, labels, and the audit script. |
| `references/slideshow.md` | The stepped presentation: focus maths, dimming, navigation. |
| `assets/diagram-template.html` | The renderer. Never carries content. |
| `assets/example-data.js` | The data shape, as a working example. |
| `scripts/fetch-gcp-icons.sh` | Google Cloud product icons, from the Iconify `gcp` mirror. |
| `scripts/build-diagram.sh` | Splices icons and data into the template. |

`fetch-gcp-icons.sh` needs `curl` and `python3`. Set `PY` to point at a
different interpreter.

## Where the icons come from

`fetch-gcp-icons.sh` reads the Iconify `gcp` collection, which mirrors Google
Cloud's product icons behind a JSON API. It is a convenience mirror; the official
library at `cloud.google.com/icons` offers current product/category icon ZIPs
and a separate legacy console collection. Use one family consistently.

Counts and coverage change. Verify required marks against the official library;
use an official asset or a clearly labeled category/neutral symbol when missing.

Iconify labels the collection Apache 2.0, and that is the wrong frame for a
trademark: section 6 of that licence excludes trademark rights. Google's terms
are a permission instead. You may use the marks to reference their technology
accurately, architecture diagrams included, and you follow their brand
guidelines when you publish one.

## The rules it will hold you to

**Measure and inspect.** Geometry catches collisions and escaping labels;
screenshots reveal weak hierarchy, poor balance and unreadable scaled text.

**Cards paint over wires.** The units layer draws last, so a connector label
running under a card is not dimmed, it is gone. This is the most common
defect, and the audit's second check exists only for it.

**One numbering system.** If the arrows count 1 to 10 and a step list beside
them counts 1 to 8, a reader who counts one lands somewhere the other does
not, and stops trusting both.

**A label must earn its place.** If the card the arrow lands on already says
`gemini-3-flash · 6 calls`, the arrow does not need the label "6 calls".
Corridor clutter is what makes these drawings look busy.

**No invented numbers.** Every figure comes from configuration, a measurement
or a document. If you cannot source it, leave it off and say so.

**Never name the addresses.** A drawing that will be served publicly or
attached to a deck must not carry project ids, service URLs, bucket paths or
internal hostnames. Describing the shape of a system is the point; handing
over its address list is not.

## What it does not do

It does not decide your architecture. Bring the inventory and the request path;
this skill draws them. For the design conversation, reach for `google-cloud-solution-architecture` (`google/skills`).

It does not draw physical objects to scale. For dimensioned orthographic
drawings of equipment and rooms, reach for `technical-drawing`.

It does not make generic HTML explainers. For diffs, plans, recaps and data
tables, reach for `visual-explainer`.

## Additional References

- [`references/google-cloud.md`](references/google-cloud.md)
- [`references/visual-design.md`](references/visual-design.md)
