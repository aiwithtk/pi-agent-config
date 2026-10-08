# Agent Access (who can run an agent)

Multica no longer uses a `workspace`/`private` visibility model. It uses **Access** — who is allowed to *run* the agent (assign it, @-mention it, or chat with it).

| Access | Who can run it |
|--------|----------------|
| `Only me` | Only the agent owner. This is the default for new agents. |
| `Entire workspace` | Every member of the workspace. |
| `Specific people` | The owner plus the selected members. |

## Key rules

- Workspace `owner`s and `admin`s can **see and manage** every agent, but **cannot bypass Access** to run someone else's "Only me" agent.
- Regular members only see agents they own or are allowed to run.
- **Seeing** an agent = ownership + workspace admin roles + Access together.
- **Modifying** = open to the agent owner and workspace owners/admins, **except Access itself**, which only the agent owner can change.
- Only the agent owner can change Access — workspace admins cannot.

## Status shown in the agent list

- **Availability** — from the runtime: `online`, `offline`, or `unstable`.
- **Workload** — from runs: `working`, `queued`, or `idle`.

"Offline" does not mean deleted; only "archived" stops new work.

## Secret configuration

- `custom_env` values are stored **plaintext server-side**; agent list/detail endpoints return only an opaque count.
- Only workspace owners/admins can unlock and modify values (audited). A running agent cannot read another agent's variables via admin endpoints.
- MCP configuration follows the same storage/display rules.
- A "private" agent's secrets are NOT masked per-visibility — the masking is uniform: env values are never returned to anyone via list/detail endpoints, regardless of Access.
