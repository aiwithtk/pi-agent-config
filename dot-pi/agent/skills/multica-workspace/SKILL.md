---
name: multica-workspace
description: CLI for managing Multica workspaces and teams — create, inspect, invite, remove members, transfer ownership, delete — with role-aware safety guards. Use for Multica workspace and team governance.
---

# multica-workspace

A CLI for workspace and team governance in Multica. It wraps the official `multica` CLI (no API keys, no extra network calls), enforces role rules (owner/admin/member), and prevents destructive operations unless explicitly confirmed.

## Key facts (current docs)

- A **workspace** is the top-level boundary: members, issues, projects, agents, skills, and run history are fully isolated per workspace.
- Creating a workspace asks for three things:
  - **Name** — shown to members, changeable later.
  - **Workspace URL / slug** — the `my-team` in `multica.ai/my-team`; lowercase letters/digits/hyphens only; **immutable after creation** (cannot collide or be reserved).
  - **Issue prefix** — e.g. `MUL` → issues are `MUL-1`, `MUL-2`; uppercase letters/digits up to 10 chars; **changeable later in settings** (renumbers every existing issue; old numbers in PRs/branch names/chat do not update).
- The creator automatically becomes an `owner`.

### Roles (owner / admin / member)

| Action | owner | admin | member |
|---|---|---|---|
| View & collaborate day-to-day | ✓ | ✓ | ✓ |
| Change workspace settings | ✓ | ✓ | — |
| Invite an admin or member | ✓ | ✓ | — |
| Change/remove an admin or member | ✓ | ✓ | — |
| Grant/revoke/remove `owner` | ✓ | — | — |
| Delete the workspace | ✓ | — | — |

- Roles only control settings/team management. Day-to-day collaboration is open to all members.
- Roles do **not** decide who can run an agent — that is the agent's own **Access** scope (owner/admin cannot bypass it).
- A workspace must always keep at least one `owner` (the last owner cannot leave/demote).
- Invitations are valid for **7 days**, grant only `admin` or `member` (an `owner` must join first and be promoted). On restricted self-hosted instances, a pending invitation allows that email to create an account.
- Removing a member deactivates their runtimes, archives the agents bound to them, cancels unfinished runs, and clears their agent-Access grants.
- Leaving a workspace deactivates runtimes you own and archives bound agents; you need a new invitation to return.
- Deleting a workspace (owner only) permanently removes all work, members, agent config, and run history — not undoable.

## Official CLI reference (`multica workspace`)

```bash
multica workspace list [--output json]
multica workspace get <slug>
multica workspace create --name "..." --slug "..."   # slug immutable
multica workspace update <slug> ...
multica workspace switch <slug>                      # set default workspace
multica workspace member list
multica workspace member invite teammate@example.com [--role admin|member]
multica workspace mcp list/add/update/remove         # workspace MCP library (owner/admin)
```

Global flags on all commands: `--server-url`, `--workspace-id`, `--profile`, `--debug`.

## Wrapper commands (local `multica-workspace`)

### `multica-workspace create`
```bash
multica-workspace create --name "My Team" --slug "my-team" --prefix "MT"
```
⚠️ The **slug** is immutable (it is the URL). The **prefix** can be changed later in settings — but changing it renumbers every issue and breaks external references (PR titles, branch names, links).

### `multica-workspace list`
```bash
multica-workspace list --output table      # default
multica-workspace list --output json
```

### `multica-workspace inspect <slug>`
Shows members, agents (with Access), issue stats, projects.

### `multica-workspace invite <slug> --email user@x.com --role [owner/admin/member]`
Blocks `--role owner` unless run by an `owner` (invitations can only grant admin/member).

### `multica-workspace remove <slug> <email>`
Blocks removal of the last `owner`.

### `multica-workspace transfer-owner <slug> --to user@x.com`
Requires confirmation and verifies the target is already a member.

### `multica-workspace agents list <slug>`
Lists agents with their Access scope (`only_me`, `workspace`, or `specific`).

## Safety guarantees
- 🔒 `--force` required for destructive commands (`delete`, `transfer-owner`, `remove`).
- 🛑 Refuses to change the workspace **slug** (immutable); the prefix is changeable but renumbers issues.
- ⚠️ `transfer-owner` verifies the target is already a member before proceeding.
- 🧯 `delete` shows the full destruction scope and requires `--force`.

## Installation
```bash
chmod +x ~/.local/bin/multica-workspace
sudo ln -s ~/.local/bin/multica-workspace /usr/local/bin/multica-workspace
```

## License
MIT
