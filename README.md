# Cabral Skills

A collection of AI coding agent skills following the [Agent Skills](https://agentskills.io) open standard. Compatible with [50+ AI coding agents](https://agentskills.io) including Cursor, GitHub Copilot, Cline, Windsurf, Gemini CLI, and more.

## Available Skills

| Skill | Description |
|---|---|
| [apigee-x-proxy-development](skills/apigee-x-proxy-development/) | Comprehensive Apigee X API proxy development — 44+ policies, flows, endpoints, fault handling, JavaScript, shared flows, caching patterns, load balancing, WebSocket/SSE, multi-tenant isolation, and more (8,300+ lines of reference documentation) |

## Installation

### Using [npx skills](https://github.com/vercel-labs/skills) (recommended)

The skills manager automatically detects your agent and installs to the right location.

```bash
# Install all skills from this collection
npx skills add carlosmscabral/cabral-skills

# Install a specific skill
npx skills add carlosmscabral/cabral-skills --skill apigee-x-proxy-development

# Install for a specific agent
npx skills add carlosmscabral/cabral-skills -a cursor
npx skills add carlosmscabral/cabral-skills -a copilot
npx skills add carlosmscabral/cabral-skills -a cline
```

### Manual installation

Copy the desired skill directory from `skills/` into your agent's skill directory:

```bash
git clone https://github.com/carlosmscabral/cabral-skills.git
cp -r cabral-skills/skills/apigee-x-proxy-development /your/agent/skills/directory/
```

## Skill Structure

Each skill follows the [Agent Skills specification](https://agentskills.io/specification):

```
skill-name/
  SKILL.md              # Metadata + instructions (loaded on activation)
  references/           # Detailed reference documentation (loaded on demand)
```

Skills use progressive disclosure: only the name and description are loaded at startup (~100 tokens). The full SKILL.md body loads when the skill activates. Reference files load only when needed during task execution.

## License

See individual skill directories for licensing information.
