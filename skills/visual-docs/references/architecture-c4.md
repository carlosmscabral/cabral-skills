# Architecture with C4 / Structurizr — consistent multi-view

When an architecture needs multiple views that **must not drift** (context →
container → component), define it **once** as a model and generate the views.
Consistency is by construction: one model, many views, and the tool enforces the C4
abstraction rules. This is the didactic ideal for architecture — the reader zooms in
without the diagrams contradicting each other.

## Why model-based

Hand-authored Mermaid diagrams drift: a service renamed in the container view but not
the context view teaches the reader something false. A C4 model has one canonical
name per element, so every generated view agrees. Use it whenever you have more than
one architecture view of the same system.

## Author `workspace.dsl`

```
workspace {
  model {
    user = person "User"
    sys  = softwareSystem "Gateway" {
      api = container "API"
      db  = container "Postgres"
    }
    user -> api "calls"
    api  -> db  "reads/writes"
  }
  views {
    systemContext sys { include *; autolayout lr }
    container sys      { include *; autolayout lr }
  }
}
```

## Validate deterministically (invalid DSL fails the command)

```bash
# Structurizr CLI (Java). Repo archived Feb 2026 but functional.
structurizr.sh export -workspace workspace.dsl -format json      # errors on bad DSL

# ...or zero-install via Kroki (Structurizr is built into the default container):
curl -s -o /dev/null -w '%{http_code}\n' -X POST "${KROKI_URL:-https://kroki.io}/structurizr/svg" \
  --data-binary @workspace.dsl -H 'Content-Type: text/plain'
```

## Export to Mermaid, then validate the output too

```bash
structurizr.sh export -workspace workspace.dsl -format mermaid    # needs Mermaid securityLevel: loose
```

Then run the exported `.mmd`/Markdown through `validate-diagrams.sh` like any other
Mermaid. Kroki can also render a chosen view directly via its `view-key` option.

## MCP (optional) — model-aware tools for the agent

The Structurizr MCP exposes DSL validation/inspection + PlantUML/Mermaid export.

- **Remote (no account):** `https://mcp.structurizr.com` — quickest, but your DSL is
  sent to Structurizr's server.
- **Local (no egress):** `docker run -it --rm -p 3000:3000 -e PORT=3000 structurizr/mcp -dsl -plantuml -mermaid`.

Enable globally (all projects):

```bash
# remote:
claude mcp add --scope user --transport http structurizr https://mcp.structurizr.com/mcp
# or local Docker (start the container first):
claude mcp add --scope user --transport http structurizr http://localhost:3000/mcp
```

Prefer the **local Docker** option for private/proprietary architectures.

## If you don't need a full model

For a single inline architecture view, a Mermaid flowchart with subgraphs is fine
(see [`diagram-type-guide.md`](./diagram-type-guide.md)). The moment you have a second
view of the same system, switch to a model so the views can't disagree. Either way,
keep **one canonical name per component** and grep every diagram to confirm they match
reality.
