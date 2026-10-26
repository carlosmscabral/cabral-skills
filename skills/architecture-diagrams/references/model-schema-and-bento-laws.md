# Model Schema, 16:9 Bento Laws & Icon Keys

## 1. Complete `model.json` Schema

```json
{
  "title": "Enterprise Agentic Platform — Runtime & Governance",
  "subtitle": "Google Cloud · southamerica-east1",
  "eyebrow": "ARCHITECTURE BLUEPRINT",
  "theme": "editorial-light",
  "layout": "pipeline-lr",
  "routing": "orthogonal",
  "gapX": 150,
  "gapY": 118,
  "boundaries": [
    {
      "id": "gcp-prod",
      "label": "Google Cloud Project · prd",
      "kind": "project",
      "children": ["apigee", "ces", "adk", "vertex", "bq"]
    },
    {
      "id": "aws-ext",
      "label": "AWS Account · External",
      "kind": "external",
      "children": ["aws-orders"]
    }
  ],
  "nodes": [
    {
      "id": "user",
      "name": "End User",
      "sublabel": "Mobile & Web App",
      "icon": "user",
      "tier": "actor",
      "description": "Customer initiating voice or chat session",
      "evidence": "docs/architecture.md"
    },
    {
      "id": "apigee",
      "name": "Apigee X",
      "sublabel": "API Gateway · mTLS",
      "icon": "gcp:apigee",
      "tier": "ingress"
    },
    {
      "id": "ces",
      "name": "Customer Engagement Suite",
      "sublabel": "Conversational Orchestrator",
      "icon": "gcp:agents",
      "tier": "compute",
      "focal": true
    },
    {
      "id": "adk",
      "name": "Cloud Run — ADK Workers",
      "sublabel": "Tool Proxies · FastAPI",
      "icon": "gcp:cloud-run",
      "tier": "compute",
      "focal": true
    },
    {
      "id": "vertex",
      "name": "Model Garden in Gemini platform",
      "sublabel": "Gemini 2.5 Flash / Pro",
      "icon": "gcp:gemini-platform",
      "tier": "ai"
    },
    {
      "id": "bq",
      "name": "BigQuery",
      "sublabel": "Conversation Analytics",
      "icon": "gcp:bigquery",
      "tier": "data"
    },
    {
      "id": "wif",
      "name": "Workload Identity Federation",
      "sublabel": "Token Exchange GCP to AWS",
      "icon": "gcp:wif",
      "tier": "external"
    },
    {
      "id": "aws-orders",
      "name": "Legacy Core API",
      "sublabel": "AWS ECS Service",
      "icon": "aws",
      "tier": "external"
    }
  ],
  "edges": [
    {"from": "user", "to": "apigee", "label": "HTTPS"},
    {"from": "apigee", "to": "ces", "label": "gRPC", "focal": true},
    {"from": "ces", "to": "adk", "label": "OpenAPI Tools", "focal": true},
    {"from": "ces", "to": "vertex", "label": "LLM Calls"},
    {"from": "ces", "to": "bq", "label": "Turn Export", "style": "dashed"},
    {"from": "adk", "to": "wif", "label": "OIDC Token"},
    {"from": "wif", "to": "aws-orders", "label": "AssumeRole"}
  ],
  "chapters": [
    {
      "title": "1. Ingress & Edge Auth",
      "nodes": ["user", "apigee", "ces"],
      "summary": "Requests enter via Apigee X with mTLS and route to the conversational orchestrator."
    },
    {
      "title": "2. Agentic Reasoning & Multi-Cloud Tools",
      "nodes": ["ces", "vertex", "adk", "wif", "aws-orders", "bq"],
      "summary": "CES invokes Gemini models and Cloud Run ADK proxies, federating to AWS via WIF."
    }
  ],
  "summary_cards": [
    {
      "title": "Security & Identity",
      "items": ["Apigee X edge authentication", "Keyless WIF bridge between Google Cloud and AWS"]
    },
    {
      "title": "Agentic Runtime",
      "items": ["Customer Engagement Suite + ADK on Cloud Run", "Model Garden in Gemini platform"]
    },
    {
      "title": "Observability & Analytics",
      "items": ["Async turn export to BigQuery", "Zero-collision orthogonal routing"]
    }
  ]
}
```

### Optional Explicit Grid Placement (`col` and `row`)
When you want exact manual control over the 2D Bento matrix, set `"col": <0..N>` and
`"row": <0..M>` on every node in `nodes[]`. When omitted, `arch_engine.py` automatically
groups nodes by `(tier, boundary)` and caps columns at 3 stacked cards.

---

## 2. The 5 Spatial & Editorial Laws

1. **Max-3-Card Vertical Ceiling**: Never stack more than 3–4 cards in a single vertical
   column (`<= 420px`). Wide widescreen (`16:9`) layouts read cleanly in slides, docs, and
   browsers.
2. **Focal Node Hierarchy (1–2 Hero Nodes Max)**: Set `"focal": true` on only the 1–2
   core components under design. Highlighting every card in a different rainbow color
   destroys visual hierarchy.
3. **Boundary Disjointness & WIF Bridge Rule**:
   - Group nodes that belong to the same `boundary` into contiguous columns/rows.
   - When connecting Google Cloud to AWS/Azure/On-Prem via **Workload Identity Federation
     (`gcp:wif`)**, keep `wif` **outside** both cloud boundaries in the channel between
     them.
4. **Unidirectional Outgoing Arrows & Short Labels (`<= 16 chars`)**:
   - Draw only outgoing request/action edges (omit redundant return arrows).
   - Keep edge `label` strings concise (`"HTTPS / JSON"`, `"MCP / gRPC"`, `"Pub/Sub"`).
5. **Executive Copywriting (No Parentheses or Pricing Math)**:
   - Avoid `()` parentheses inside card titles, sublabels, or edge labels (`arch_engine.py`
     automatically normalizes `(` and `)` to clean separators).
   - Never put dollar figures (`$`), GSU counts, or token formulas inside diagram boxes.
   - Use current Google Cloud naming: **Google Cloud** (never "GCP" in rendered titles),
     **Gemini platform**, **Model Garden in Gemini platform**, **Agent Runtime in Gemini
     platform**.

---

## 3. Supported Boundary `kind` Styles

| `kind` | Visual Purpose |
|---|---|
| `"project"` | Dashed Google Blue (`#1a73e8`) border for a Google Cloud Project |
| `"vpc"` | Dashed Slate (`#64748b`) border for a VPC Network or Subnet |
| `"zone"` | Soft Blue (`#e8f0fe`) container for Ingress / Perimeter / Compute zones |
| `"execution"` | Soft Coral (`#fce8e6`) container for Agent / Execution runtimes |
| `"governance"` | Soft Green (`#e6f4ea`) container for Core Governance / Control Plane |
| `"data"` | Soft Amber (`#fef7e0`) container for Data / Storage / Connected Tools |
| `"external"` | Dashed Warm Amber (`#f59e0b`) container for AWS / Azure / On-Prem / SaaS |
| `"c4-system"` | Dashed C4 System Scope boundary |
| `"c4-container"` | Dashed C4 Container Scope boundary |

---

## 4. Built-in Verbatim Icon Keys (`icon`)

Pass any of these keys in `"icon"` (with or without `gcp:` prefix):
- **AI & Agents**: `agents`, `adk`, `ces`, `gemini`, `gemini-platform`, `vertex-ai`,
  `aiml`, `ai-hypercomputer`
- **Compute & Containers**: `cloud-run`, `gke`, `compute-engine`, `serverless`
- **Integration & Edge**: `apigee`, `api-gateway`, `cloud-load-balancing`, `cloud-cdn`,
  `cloud-dns`, `integration-services`
- **Data & Databases**: `bigquery`, `spanner`, `alloydb`, `cloud-sql`, `databases`,
  `cloud-storage`, `pubsub`, `dataflow`, `dataplex`, `looker`, `hyperdisk`
- **Security & Networking**: `wif`, `iam`, `cloud-armor`, `scc`, `security`, `secops`,
  `mandiant`, `threat-intelligence`, `vpc`, `networking`, `hybrid-multicloud`
- **DevOps & Operations**: `devops`, `developer-tools`, `observability`, `operations`
- **Multi-Cloud & Generic**: `google-cloud`, `aws`, `aws-s3`, `azure`, `sharepoint`,
  `onprem`, `external-api`, `user`, `client`, `mcp`
