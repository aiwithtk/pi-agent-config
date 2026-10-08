# Critical Security Rules

⚠️ These rules are enforced by `multica-agent` and must never be bypassed:

## 1. `custom_env` is strictly filtered
- Blocked keys: `PATH`, `HOME`, `USER`, `SHELL`, `TERM`, `CODEX_HOME`
- Blocked prefixes: `MULTICA_`
- Values are stored in plaintext on the server → never store production secrets (use scoped, short-lived tokens)

## 2. GitHub/ClawHub skills require `--i-understand-risks`
- The "ClawHavoc" incident (Feb 2026) showed malicious skills can steal API keys.
- Multica does not sandbox or audit third-party skills — they run as-is.
- Always review `SKILL.md` and every file before importing.

## 3. Archiving cancels all in-flight tasks
- `multica-agent archive <id>` immediately marks queued, dispatched, and running tasks as `cancelled`.
- No confirmation bypass — interactive `YES` required.

🔐 This skill prioritizes safety over convenience — because agent misconfiguration can leak credentials or waste compute.
