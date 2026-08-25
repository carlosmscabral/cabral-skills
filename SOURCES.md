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

### Agents365-ai/drawio-skill — natural language to editable Draw.io diagrams & exports
Generates editable `.drawio` XML diagrams (UML, C4, architecture, sequence, ERD, ML) from prompts,
codebases (Python/TS/Go/Rust), Terraform/K8s/Docker configs, and SQL DDL. Includes vision
self-correction and exports to PNG/SVG/PDF/JPG. MIT.

**1. Prerequisites (Draw.io desktop CLI):**
```bash
# macOS
brew install --cask drawio

# Linux (headless export needs xvfb)
sudo apt install xvfb
# Download .deb from https://github.com/jgraph/drawio-desktop/releases
```
Verify with `drawio --version` (version >= 30 recommended for Mermaid-to-Draw.io and ELK layout support).

**2. Install:**
```bash
# Via npx skills (global or per-agent)
npx skills add Agents365-ai/365-skills -g

# Or direct clone into agent skills directory
git clone https://github.com/Agents365-ai/drawio-skill.git ~/.gemini/config/skills/drawio-skill
# (or ~/.claude/skills/drawio-skill for Claude Code)
```

**3. Update:**
```bash
# Via skills CLI
skills update drawio-skill

# Or git pull
cd ~/.gemini/config/skills/drawio-skill && git pull

# Claude Code plugin marketplace
/plugin update drawio
```

---

## How to add a pointer here

Keep entries short: **name → one-line why → exact install command**. If I find myself needing to
*modify* or *pin* an external thing (not just install it), that's the signal to stop pointing and
start vendoring it inside a plugin instead — see the "blend plugin" recipe in
[AGENTS.md](AGENTS.md).
