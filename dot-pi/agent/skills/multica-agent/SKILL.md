---
name: multica-agent
description: CLI for managing Multica agents — create, list, inspect, update, archive, restore, copy, and attach skills — with Access-aware controls and safety guards. Use for Multica agent governance.
---

# multica-agent

A CLI for agent governance in Multica. It wraps the official `multica` CLI (no API keys, no extra network calls) and enforces safety rules: never expose `MULTICA_*` env vars, never store secrets in `custom_args`, and never perform destructive operations without confirmation.

## Mental model (official docs)

- **Agent** = a reusable *identity + configuration* (name, instructions, model, skills, Access, runtime). It is **not** a long-running process — it only executes when triggered (issue assignment, @-mention, chat, or Autopilot).
- **Runtime** = the computer + AI coding tool that actually executes the run.
- **Run** = one concrete execution record. One agent → many runs; one runtime → many agents; an offline runtime keeps the agent's identity/history but new runs wait.

## Key facts (current docs)

- Creating an agent requires only **name** (unique within the workspace) + **runtime**. Everything else has defaults.
- **Access** — who can *run* the agent (this replaces the old "visibility" model):
  - `Only me` — default; only the owner.
  - `Entire workspace` — every member.
  - `Specific people` — owner + selected members.
  - Workspace owners/admins can *see and manage* all agents, but **cannot bypass Access** to run someone else's "Only me" agent. Only the agent owner can change Access.
- **Availability vs workload**: availability comes from the runtime (online/offline/unstable), workload from runs (working/queued/idle). "Offline" ≠ deleted — only "archived" stops new work.
- **Concurrency**: agent cap default **6**; daemon-wide cap default **20**; effective = the smaller of the two.
- **`custom_env` is stored in plaintext server-side** and sent to the runtime at execution time. List/detail endpoints return only an opaque count; only workspace owners/admins can unlock and modify values (every read/change is audited). `PATH`, `HOME`, `MULTICA_*`, and other critical runtime vars cannot be overridden. Do not put high-value long-lived credentials here.
- **`custom_args`** are appended item-by-item with **no shell expansion**. Never put credentials there — they remain in the child process argv (visible via `ps`/`/proc`). Use `custom_env` instead.
- **MCP config** may contain tokens; same storage/display rules as env vars. Only shown for tools that support managed MCP.
- **Archiving** removes the agent from pickers, cancels *all* unfinished runs (queued + running), preserves history, and can be restored. Owner + workspace owners/admins can archive/restore.
- **`agent copy`** carries over instructions, conversation starters, skills, args, avatar, concurrency, and Access — but **never** `custom_env`, `mcp_config`, or `runtime_config` (must be re-set). If forced onto another runtime, model/thinking-level/service-tier are cleared and must be re-selected.

## Official CLI reference (`multica agent`)

```bash
multica agent list [--output json|table]
multica agent get <agent-id>
multica agent create --name "Frontend Reviewer" --runtime-id <id> \
  --description "..." --instructions "..." \
  --conversation-starters '[{"label":"Review a PR","prompt":"..."}]' \
  --model ... --thinking-level ... --mcp-config ... --permission-mode ... \
  --max-concurrent-tasks 6
multica agent update <agent-id> ...
multica agent copy <agent-id> [--name] [--runtime-id] [--no-skills]
multica agent archive <agent-id>
multica agent restore <agent-id>
multica agent tasks <agent-id>                 # runs
multica agent avatar <agent-id>
multica agent env get <agent-id>               # owner/admin only
multica agent env set <agent-id>
multica agent skills list <agent-id>
multica agent skills set <agent-id> --skill-ids <id>   # replaces full list
multica agent skills add <agent-id> --skill-ids <id>   # appends
multica agent mcp list/add/enable/disable/remove <agent-id>
```

Issue keys use `MUL-123` or full UUIDs; short UUID prefixes are not accepted. Scripts should use `--output json`, not parse tables.

## Wrapper commands (local `multica-agent`)

### `multica-agent create`
```bash
multica-agent create --name "Code Reviewer" --runtime rt_xxx --access workspace
```
Tip: `multica-agent create --list-runtimes` shows available runtimes.

### `multica-agent list`
```bash
multica-agent list --output table      # default
multica-agent list --output json
multica-agent list --status online     # agents with active runtimes
```

### `multica-agent inspect <id>`
Full details: config, runtime, skills, health. Warns when the agent uses a tool without session resumption.

### `multica-agent update <id>`
```bash
multica-agent update ag_123 --env ANTHROPIC_API_KEY=sk-... --arg "--max-turns" "100" --concurrency 3
```
⚠️ Blocks `MULTICA_*`, `PATH`, `HOME`, `SHELL`, `USER`, `TERM`. `--i-understand-risks` required for unsafe keys.

### `multica-agent archive <id>` / `multica-agent restore <id>`
Archive cancels all in-flight tasks (queued + running); restore brings it back.

### `multica-agent skills list <id>` / `multica-agent skills add <id>`
```bash
# From a URL (⚠️ review first!)
multica-agent skills add ag_123 --source github --url https://github.com/owner/repo/tree/main/skills/x --i-understand-risks
# From a local path
multica-agent skills add ag_123 --source local --path ./my-skill
```

## Safety guarantees
- 🔒 `--i-understand-risks` required for external skill imports (GitHub/ClawHub/Skills.sh/URL).
- 🛑 `custom_env` blocks `MULTICA_*`, `PATH`, `HOME`, `SHELL`, `USER`, `TERM`.
- ⚠️ `inspect` warns on tools that lack session resumption.
- 🧯 `archive` shows "This will cancel N running tasks. Continue? [YES/no]".

## Installation
```bash
chmod +x ~/.local/bin/multica-agent
sudo ln -s ~/.local/bin/multica-agent /usr/local/bin/multica-agent
```

## License
MIT
