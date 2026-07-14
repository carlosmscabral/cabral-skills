---
trigger: always_on
description: Mandatory cryptographic security checks and credentials prevention rules
---
# Cryptographic and Secrets Prevention

*   Never write, logging, or leak API keys, credit card numbers, SPIFFE keys, or PII into text files, terminal outputs, or thoughts.
*   All config variables must be read from `.env` template definitions.
