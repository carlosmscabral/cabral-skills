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

---

## How to add a pointer here

Keep entries short: **name → one-line why → exact install command**. If I find myself needing to
*modify* or *pin* an external thing (not just install it), that's the signal to stop pointing and
start vendoring it inside a plugin instead — see the "blend plugin" recipe in
[AGENTS.md](AGENTS.md).
