# SOURCES.md — external skills & plugins I use

Curated pointers to third-party skills/plugins I like but **don't vendor** here. Each entry is
installed fresh from its own upstream — this file is just the shortlist + the exact command, so I
don't have to rediscover them. (Things I *do* vendor live inside a plugin and are tracked in
[`vendored.json`](vendored.json); see [AGENTS.md](AGENTS.md).)

## Plugins (`agy plugin install`)

### obra/superpowers — spec-driven development methodology
Full SDLC methodology (14 skills): brainstorming → writing-plans → executing-plans → TDD →
code-review → verification, plus an always-on bootstrap rule. MIT. All-or-nothing; adds a small
always-on token tax per session. Install globally from upstream:

```bash
agy plugin install obra/superpowers
```

> I previously vendored this whole repo into cabral-skills; that snapshot now lives in
> [`archive/superpowers/`](archive/superpowers/) (pinned at v6.1.1 / commit `c984ea2`). The
> pointer above is the maintained path — prefer it.

## Skills (`npx skills add`)

### google/skills — Google's official skill collection
General-purpose Google/GCP skills. Browse and pick what's relevant:

```bash
npx skills add google/skills                 # all
npx skills add google/skills --skill <name>  # one
```

### External diagramming references (consolidated into `skills/architecture-diagrams/`)
Core system/cloud architecture diagramming, Dual-Mode `.drawio.svg` / multi-page C4 `.drawio` XML generation, and interactive HTML exploration are now natively handled by our own zero-dependency [`skills/architecture-diagrams/`](skills/architecture-diagrams/) skill (while didactic Markdown/Mermaid/ASCII explanations live in [`skills/visual-docs/`](skills/visual-docs/)). The external community projects below served as design inspiration and remain useful references:

- **[Agents365-ai/drawio-skill](https://github.com/Agents365-ai/drawio-skill)** — Multi-page C4 (L1–L4) `.drawio` conventions, port separation (`exitX`/`exitY`/`entryX`/`entryY`), and Draw.io Desktop CLI export patterns (`npx skills add Agents365-ai/365-skills -g`).
- **[tt-a1i/archify](https://github.com/tt-a1i/archify)** — Interactive HTML architecture explorer patterns (guided walkthrough chapters, node click inspector, upstream/downstream path highlighting, and evidence badges).
- **[cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design)** — Bento Grid composition laws, orthogonal routing with rounded corners (`r=8px`), perpendicular arrowheads, and masked edge labels.

---

## How to add a pointer here

Keep entries short: **name → one-line why → exact install command**. If I find myself needing to
*modify* or *pin* an external thing (not just install it), that's the signal to stop pointing and
start vendoring it inside a plugin instead — see the "blend plugin" recipe in
[AGENTS.md](AGENTS.md).
