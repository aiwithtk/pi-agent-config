---
name: multica-issues
description: Manage Multica issues, comments, projects, and project resources — statuses and lifecycle categories, custom statuses, sub-issues and stages, @-mentions, PR linking, and the full CLI reference. Use when working with Multica issues, projects, or project resources.
---

# multica-issues

Reference for Multica's work objects — **issues**, **comments**, **projects**, and **project resources** — and the four ways to trigger agents. Everything here is driven by the official `multica` CLI.

## Issues

An issue is the basic unit of work: a feature, bug, or investigation owned by a member, an agent, or a squad. It holds title/description, status/priority, assignee, dates, labels, custom properties, project & parent-child relationships, and the activity + execution log.

### Built-in statuses (7) and lifecycle categories (4)

| Category | Statuses | Meaning |
|---|---|---|
| `unstarted` | `backlog`, `todo` | not started |
| `started` | `in_progress`, `in_review`, `blocked` | ongoing |
| `done` | `done` | terminal success |
| `closed` | `cancelled` | terminal, not success |

- **`backlog` is special**: an issue assigned to an agent only creates a run **after** it leaves `backlog`. A custom status in `unstarted` does NOT park work.
- Agents write status as their work changes: starting → `in_progress`, delivering → `in_review`, continuing → stays `in_progress`, consulting → status untouched. `done` is usually human confirmation or a merged closing PR.
- Two system changes: a failed run with no retry rolls `in_progress` back to `todo`; when every linked PR merges and one uses a closing keyword, the issue becomes `done`.
- Custom statuses: owner/admin can add them (Settings → Issue Statuses). A status's category is fixed at creation; built-in statuses are locked. Address by key: `multica issue status MUL-42 code_review`.
- Sub-issues can carry a **stage** (1/2/3); when all sub-issues in the earliest unfinished stage reach `done`/`cancelled`, the parent notifies (and wakes an agent assignee to start the next stage).

## Triggering agents (four ways)

1. **Assign the issue** to an agent or squad — it starts when the issue is `todo` or later.
2. **@-mention** in a comment — handles that request without changing the assignee.
3. **Direct chat** — each message = one run, no issue.
4. **Autopilot** — schedule or webhook.

Shared rules: you can only trigger agents you have permission to run (**Access**, not role); a **trigger preview** shows who will wake; `/note` posts without triggering; `backlog` does not trigger.

## Comments

- Replying forms a discussion thread. Members who comment auto-subscribe to the issue.
- @-targets: **member** = inbox notification; **agent** = creates a run; **squad** = notifies members + triggers leader; **issue** = inserts a link; **@all** = notifies members, triggers no agent.
- Agents have no inbox; an @-mention of an agent is a trigger, not a notification.
- Comment authors can edit/delete their own; owners/admins can edit/delete anyone's; agent comments can only be deleted, not edited.
- After editing, triggers are recalculated from the new content.

## Projects

- Groups related issues under one goal; progress = `(done + cancelled) ÷ all issues`. Project status is independent of issue status.
- Fields: name/icon/description (enters agent run context), status (`planned`/`in_progress`/`paused`/`completed`/`cancelled`), priority, **lead** (member or agent — coordination only, not a permission), dates, issues, resources.
- An issue belongs to at most one project; moving it doesn't copy it. Only owner/admin can delete a project (issues detach, not delete).

## Project resources

Two types: **GitHub repo** (`github_repo`) or **local directory** (`local_directory`).

- `github_repo` uses **worktree mode by default** → unlimited concurrent runs; result is a branch `agent/<agent>/<issue>`.
- `local_directory` (Desktop-only UI) has two modes:
  - `in_place` (default, "Direct") — agent works directly in your dir; **one run at a time** (others enter `waiting_local_directory`).
  - `worktree` ("Parallel") — per-run git worktrees, concurrent, hands back a branch. Requires a git repo with ≥1 commit. Local edits/uncommitted files are replayed into the worktree.
- Rejected local paths: `/`, `C:\`, home dirs, parents of home, `/etc`, `/var`, `/tmp`, `/usr`, `/opt`. Symlinks resolve to real path first.
- Only one local directory per daemon per project.
- Resources are added to run context; `.multica/project/resources.json` is written into the working directory.

## CLI reference

```bash
# Issues
multica issue list [--status --priority --assignee --project --metadata --property --limit --sort --full-id]
multica issue get MUL-123 [--resolve-properties]
multica issue create --title "..." [--description|--description-stdin|--description-file] [--status --priority --assignee --parent --stage --project --due-date --attachment]
multica issue update MUL-123 ... [--position --no-start]
multica issue assign MUL-123 --to "Agent name" | --to-id <uuid> [--no-start] | --unassign
multica issue status MUL-123 in_progress [--no-start]
multica issue reorder MUL-123
multica issue search "login failure" [--include-closed]
multica issue children MUL-123
multica issue pull-requests MUL-123
multica issue comment list/add/delete/resolve/unresolve MUL-123
multica issue subscriber list/add/remove MUL-123
multica issue label list/add/remove MUL-123
multica issue metadata list/get/set/delete MUL-123
multica issue property list/set/unset MUL-123
multica issue runs MUL-123
multica issue run-messages <task-id> --issue MUL-123
multica issue usage MUL-123
multica issue rerun MUL-123            # fresh session + working dir, current assignee
multica issue cancel-task <task-id> --issue MUL-123

# Projects
multica project list/get/create/update/delete
multica project status <id> <status>
multica project resource list <project-id>
multica project resource add <project-id> --type github_repo --url <url> [--ref main]
multica project resource add <project-id> --type local_directory --local-path /abs/path --daemon-id <id> [--execution-mode worktree|in_place]
multica project resource update <project-id> <resource-id> --execution-mode worktree
multica project resource remove <project-id> <resource-id>

# Labels & custom properties
multica label list/get/create/update/delete [--resource-type issue|skill]
multica property list/get/create/update/archive/unarchive
multica property create --name "..." --type text|number|select|multi_select|date|checkbox|url|actor|multi_actor --option "A"
```

- Issue keys use `MUL-123` or full UUIDs; short UUID prefixes are not accepted.
- Read long text from stdin/files (`--description-stdin`, `--content-stdin`, `--content-file`) to avoid quoting issues.
- `--no-start` records ownership without creating a run (also on `issue update` and `issue status`).
- `multica issue rerun` uses the current assignee with a fresh session; retrying a specific run keeps the original agent.

## License
MIT
