# Draw.io Export, Dual-Mode `.drawio.svg` & Multi-Page C4 Guide

## 1. Dual-Mode `.drawio.svg` vs Native `.drawio`

Every run of `arch_engine.py build` produces **both** Draw.io formats automatically:

1. **`<name>.drawio` (Native `mxGraphModel` XML)**:
   - Best when opening directly in [https://drawio-internal.corp.goog/](https://drawio-internal.corp.goog/)
     (`go/draw-io`) or desktop `draw.io` to drag individual cards, edit labels, or browse
     multiple C4 tabs (`Page 1`, `Page 2`, `Page 3`).
   - Uses attached child icon cells (`part=1;connectable=0;image=data:image/svg+xml,<B64>`)
     and `spacingLeft=56` so every card carries its official 4-color vector icon and drags
     as a single unit.
2. **`<name>.drawio.svg` (Dual-Mode Vector SVG + Embedded `<mxfile>`)**:
   - Best when committing to Git/GitHub, embedding in Markdown/g3doc, or uploading to
     Google Drive.
   - Browsers and Markdown viewers render the outer `<svg>` at 100% crisp vector quality,
     while `draw.io` and Google Drive (*Open with → diagrams.net*) read the XML-escaped
     `<mxfile>` inside `<svg content="...">` so the exact same `.drawio.svg` file opens as
     an editable Draw.io diagram without *"Not a diagram file"* errors!

### Crucial Draw.io Style Invariant (Enforced by `arch_engine.py check`)
In `mxGraph` (`<mxCell style="...">`), semicolons (`;`) delimit key-value pairs. Never
write `image=data:image/svg+xml;base64,<B64>;` — the parser splits on `;base64` and breaks
the icon. Always use `image=data:image/svg+xml,<B64>;` (without `;base64`).

---

## 2. Multi-Page C4 Architecture Models (`L1 / L2 / L3`)

To generate a multi-tab C4 model (or multi-view architecture such as *Executive*,
*Dataflow*, and *Security* views) in a single `.drawio` and interactive `.html` explorer,
use the top-level `"pages"` array in `model.json`:

```json
{
  "theme": "editorial-light",
  "pages": [
    {
      "page_name": "1 - System Context (L1)",
      "title": "Order Platform — L1 System Context",
      "subtitle": "C4 Level 1 · System Context",
      "boundaries": [
        {"id": "sys-scope", "label": "Enterprise Boundary", "kind": "c4-system", "children": ["order-sys"]}
      ],
      "nodes": [
        {"id": "customer", "name": "Customer", "sublabel": "Person · Web/Mobile", "icon": "user", "tier": "actor"},
        {"id": "order-sys", "name": "Order Management System", "sublabel": "Software System", "icon": "gcp:google-cloud", "tier": "compute", "focal": true},
        {"id": "sap-erp", "name": "SAP ERP", "sublabel": "External System", "icon": "onprem", "tier": "external"}
      ],
      "edges": [
        {"from": "customer", "to": "order-sys", "label": "Places orders"},
        {"from": "order-sys", "to": "sap-erp", "label": "Syncs invoices"}
      ]
    },
    {
      "page_name": "2 - Containers (L2)",
      "title": "Order Platform — L2 Container View",
      "subtitle": "C4 Level 2 · Deployable Units",
      "boundaries": [
        {"id": "sys-l2", "label": "Order Management System", "kind": "c4-container", "children": ["api-gw", "order-svc", "order-db", "events"]}
      ],
      "nodes": [
        {"id": "customer", "name": "Customer", "sublabel": "Person", "icon": "user", "tier": "actor"},
        {"id": "api-gw", "name": "Apigee API Gateway", "sublabel": "Container · Apigee X", "icon": "gcp:apigee", "tier": "ingress"},
        {"id": "order-svc", "name": "Order Service", "sublabel": "Container · Cloud Run", "icon": "gcp:cloud-run", "tier": "compute", "focal": true},
        {"id": "order-db", "name": "Orders Database", "sublabel": "Container · Cloud Spanner", "icon": "gcp:spanner", "tier": "data"},
        {"id": "events", "name": "Order Events Topic", "sublabel": "Container · Pub/Sub", "icon": "gcp:pubsub", "tier": "data"}
      ],
      "edges": [
        {"from": "customer", "to": "api-gw", "label": "HTTPS JSON"},
        {"from": "api-gw", "to": "order-svc", "label": "gRPC"},
        {"from": "order-svc", "to": "order-db", "label": "Reads/Writes"},
        {"from": "order-svc", "to": "events", "label": "Publishes", "style": "dashed"}
      ]
    }
  ]
}
```

### Strict C4 Granularity Rules
- **Level 1 (`System Context`)**: Only `Person`, target `Software System`, and `External
  Software Systems`.
- **Level 2 (`Container`)**: Only **independently deployable/runnable units or data
  stores** (Web App, API Gateway, Cloud Run Service, GKE Workload, Spanner DB, Pub/Sub
  Topic). Never put internal classes, functions, or in-process helpers in Level 2!
- **Level 3 (`Component`)**: Zoom into **one single Container** to show its internal
  controllers, domain services, validators, and repositories.

---

## 3. When to Combine with `Agents365-ai/drawio-skill`

`arch_engine.py` handles 95% of architecture diagramming, Mermaid conversion, C4 modeling,
and `.drawio` / `.drawio.svg` generation with zero bloat. If a task specifically requires
**automated AST/config scraping from a massive directory of raw `.tf` Terraform state,
Helm/K8s manifests, GraphQL SDL, or SQL DDL**, you can optionally invoke the external
`Agents365-ai/drawio-skill` documented in the repository's `SOURCES.md`.
