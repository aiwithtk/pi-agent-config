# Critical Security Rules

⚠️ These rules are enforced by `multica-workspace` and must never be bypassed:

## 1. Issue Prefix is Immutable
- The `issue_prefix` (e.g., `MUL`) is set at workspace creation and **cannot be changed**.
- Changing it breaks every external link, Slack mention, and historical reference (`MUL-5` → `NEW-5`).
- `multica-workspace create` validates `--prefix` (uppercase only) but does **not expose any `update-prefix` command**.

## 2. Owner Transfer Must Preserve At Least One Owner
- You cannot demote or remove the last owner.
- `multica-workspace transfer-owner` verifies the target email is already a member *before* proceeding.
- If you’re the last owner and want to leave: first transfer ownership, *then* remove yourself.

## 3. Destructive Actions Require `--force`
- `delete`, `transfer-owner`, and `remove` all require explicit confirmation + `--force` flag in production use.
- Interactive confirmation is mandatory in CLI mode.

🔐 This skill prioritizes safety over convenience — because workspace deletion is irreversible.
