# Slides and export

The HTML renderer creates a browser presentation. For actual Google Slides or
PPTX, use an available presentation skill/tool with this skill's diagram semantics.
If direct Google Slides creation is unavailable, offer an editable PPTX for import
and state clearly that no live Google Slides document was created.

Use native text, shapes, containers and connectors for editable slides; product
icons may be embedded SVG/PNG. A slide-sized screenshot is not an editable diagram.
Preserve stable IDs in source data and meaningful object names where supported.
Verify import fidelity before claiming an imported deck was tested.

## Storyboard

Overview and thesis → main request/event journey → relevant security, failure or
operations detail → whole-system recap and supported takeaway. Adapt slide count
to the story. A concern view can highlight multiple edges; only main journey steps
need to match numbered edges. Notes carry rationale, evidence and assumptions.

## Export checks

- Default to 16:9 unless another ratio is requested. Use consistent safe margins
  and projection-sized labels.
- Render every slide; inspect wrapping, connectors, cropping and font substitution.
- Export diagram images undimmed, with a legend and adequate resolution. Ensure
  embedded icons and SVG styles survive export.
- HTML print mode prints an undimmed overview, not a multi-page slide deck.
- Confirm editable deck labels/connectors are native objects. Keep private
  identifiers out of public notes and source data as well as visible slides.
