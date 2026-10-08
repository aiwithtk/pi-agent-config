---
name: multica-squads
description: Manage Multica squads — leader, members, role descriptions, squad instructions, the leader operating protocol, delegation rules, and the CLI. Use for Multica squad governance and multi-agent coordination.
---

# multica-squads

Reference for **squads**: a leader agent plus members (agents or humans) that coordinates multi-agent work. Assigning an issue to a squad wakes **only the leader**; it decides who takes the next step.

## Structure

| Setting | What it does |
|---|---|
| **Leader** | Must be an agent. Receives squad-assigned work and decides how to handle it. |
| **Members** | Agents or human members; the same member can join multiple squads. |
| **Role descriptions** | One line per member telling the leader what each is suited for. Context only — grants no permissions, never triggers members automatically. |
| **Squad instructions** | Routing rules, collaboration norms, squad-wide background. Provided to the **leader only**. |

Creating a squad requires a **name + leader**. The leader automatically becomes a member.

## How a squad run works

1. Non-`backlog` issue assigned to a squad → run enqueued for the **leader only** (not every member).
2. On claim, the leader's system prompt gets three appended blocks (see below).
3. Leader posts **one delegation comment** @-mentioning the chosen member(s) — the mention triggers a run for each mentioned agent.
4. Leader records its evaluation: `multica squad activity <issue-id> action --reason "..."`.
5. Dispatch leaves the parent `in_progress` (dispatch ≠ delivery). The leader only moves it to `in_review` once the overall goal is met; `done` is left to a human or a merging PR.

## What the leader sees on every turn

- **Squad Operating Protocol** (system-managed, not editable): read the issue, delegate by @-mention, be terse, record an evaluation every turn, **stop after dispatching**, move parent to `in_review` only when the goal is met.
  - The status half is scoped to issues assigned to this squad — a leader woken by an `@squad` mention on someone else's issue gets the roster/delegation rules but is told **not** to touch that issue's status.
- **Squad Roster** — exact mention markdown per member (`[@Name](mention://agent/<uuid>)` / `member/<uuid>`). Typing a plain `@name` won't trigger anyone.
- **Squad Instructions** — your custom routing/escalation guidance.

## Leader re-trigger rules (after first dispatch)

| Event | Leader triggered? |
|---|---|
| Non-member (human reporter / external agent) posts a comment | ✅ yes |
| Squad member posts a progress update with no @mention | ✅ yes — re-evaluates |
| A comment explicitly @-mentions another agent/member/squad/`@all` | ❌ no — the explicit @ is the routing signal |
| The leader's own comment (self-trigger) | ❌ no (loop guard) |
| A comment with only an issue cross-reference | ✅ yes |
| Agent-authored comment that @s another agent | ✅ yes (leader coordinates the thread) |

Dedup: if the leader already has a `queued`/`dispatched` run on the issue, a new trigger won't enqueue a duplicate.

## Permissions & lifecycle

- Any member can create a squad. Creators can modify/archive their own; owners/admins manage all.
- Adding an agent to a squad does not bypass its **Access**. Whether a member can assign/@-mention a squad depends on whether they can run the squad's **leader**.
- Squad names need not be unique. Changing the leader makes the new leader join automatically; the current leader can't be removed directly — designate another first.
- **Archiving is permanent** (cannot be restored). Issues/automations assigned to the squad transfer to the former leader agent.

## CLI reference

```bash
multica squad create --name "Product Delivery" --leader delivery-lead
multica squad list/get
multica squad update <id> --instructions "..."
multica squad delete <id>                 # archives
multica squad member list <id>
multica squad member add <id> --member-id <agent-or-member-id> --type agent|member --role "Owns frontend"
multica squad member set-role <id> <member-id> --role "..."
multica squad member remove <id> <member-id>
multica squad activity <issue-id> action --reason "..."   # leader records an evaluation
```

## License
MIT
