---
trigger: always_on
description: Strict air-gapped zero network constraints for banking environments
---
# Air-Gapped Network Constraints

*   You are strictly forbidden from initiating or requesting external URL reads or writes (`read_url`, `execute_url` are blocked).
*   All libraries and dependencies must be retrieved exclusively from pre-audited, internal artifactories. Never request `pip install` or `npm install` on public mirrors.
*   You must assume every terminal execution is sandboxed using isolated gVisor/Docker nodes.
*   Do not attempt to execute administrative or system-level scripts natively. Only run low-privilege workspace actions.
