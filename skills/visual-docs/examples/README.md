# Examples — validated, narrated visual explanations

Four worked examples, one per major teaching mode. Each pairs a diagram with
narration (what / read-order / key / omitted), includes an ASCII fallback, and its
Mermaid compiles. Use them as templates.

| File | Teaches | Primary form |
|---|---|---|
| [01-request-flow.md](./01-request-flow.md) | A request lifecycle with decisions | Flowchart (+ ASCII) |
| [02-auth-sequence.md](./02-auth-sequence.md) | An OAuth token handshake | sequenceDiagram (+ ASCII) |
| [03-tcp-packet-walk.md](./03-tcp-packet-walk.md) | Reading a TCP header + handshake | ASCII packet walk (+ sequence) |
| [04-code-explainer.md](./04-code-explainer.md) | How a function executes | Annotated code + call graph + trace |

## Validate them (the "test")

From the repo root:

```bash
skills/visual-docs/scripts/validate-diagrams.sh skills/visual-docs/examples/ skills/visual-docs/references/
# expect a final line like:  diagrams: N   failed: 0
```

The validator auto-detects a backend (`mmdc` → `npx` → Kroki HTTP). ASCII diagrams
need no compiler; they live in fenced code blocks so spacing is preserved.
