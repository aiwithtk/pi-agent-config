---
name: multica-autopilots
description: Manage Multica autopilots — schedules, webhook triggers, execution modes, event filters, idempotency, and run history. Use for Multica automation and scheduled/recurring agent work.
---

# multica-autopilots

Reference for **autopilots**: recurring work that runs on a **schedule** or a **webhook** (or manually). Each autopilot stores a Runbook, an assignee, and one or more triggers.

## Configuration

| Field | What it does |
|---|---|
| **Name** | What the autopilot is responsible for |
| **Runbook** | Goal, background, constraints, steps the agent reads on every run |
| **Assignee** | An agent or a squad |
| **Project** | optional; puts auto-created issues into a project |
| **Execution mode** | `create issue` (default) or `run only` |
| **Subscribers** | members notified after an issue is auto-created |
| **Triggers** | a schedule and/or a webhook |

Enabled by default after saving; **Run now** executes the full flow once.

## Execution modes

| Mode | Behavior | Best for |
|---|---|---|
| **Create issue** | Each trigger first creates an issue, then assigns it; discussion/status/runs live on the issue. Works even if the runtime is offline (run queues). | Work the team reviews/follows up on |
| **Run only** | Creates a run directly, no issue; results only in the autopilot run history. Requires runtime available at trigger time, else **skipped**. | Background runs, no collaboration record |

`run only` mode does not auto-retry (to avoid overlapping the next schedule). `create issue` produces regular issue runs that retry under normal rules.

## Schedules (cron)

Standard 5-field cron: `minute hour day month weekday`. No seconds. IANA timezones (`Asia/Shanghai`).

```
0 9 * * 1-5        # 9:00 weekdays
*/30 * * * *       # every 30 min
0 3 * * *          # 3:00 daily
```

One autopilot can have multiple schedules; enable/disable a single trigger via `multica autopilot trigger-update`.

## Webhooks

After adding a webhook trigger, Multica generates a unique URL. POST a JSON object or array (max **256 KiB**):

```bash
curl -X POST "$MULTICA_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: demo-001" \
  -d '{"event":"build.completed","eventPayload":{"status":"success"}}'
```

- **`Idempotency-Key`** prevents duplicate runs on sender retries; GitHub deliveries also dedup by `X-GitHub-Delivery`.
- **Rotate the URL** if it leaks (`autopilot trigger-rotate-url`); the old URL stops immediately.
- **Event filters**: each row = event name + optional actions; a run fires if any row matches; empty rows accept every event. Inference order: body `event` → `X-GitHub-Event` (+body `action`) → `X-Gitlab-Event` → `X-Event-Type` → body `event`/`type`/`action` → `webhook.received`.

### Webhook response codes

| HTTP | status | Meaning |
|---|---|---|
| 200 | `accepted` | run created |
| 200 | `skipped` | accepted but skipped (e.g. runtime offline in run-only) |
| 200 | `ignored` | trigger disabled/paused/archived or event filtered |
| 200 | `duplicate` | idempotency key hit an existing delivery |
| 400 | — | empty / invalid JSON / not object-array |
| 401 | `rejected` | signing secret configured but signature missing/mismatched |
| 404 | — | token invalid or rotated |
| 413 | — | body exceeds 256 KiB |
| 429 | — | rate limited (`Retry-After`) |
| 500 | — | internal error |

Business-level ignores return 200 (not 4xx) so senders don't retry endlessly. A processed webhook delivery can be **replayed** from its detail view (creates a new delivery/run, no dedup).

## Automatic pause

If the past 7 days have ≥50 completed/failed runs with a **90% failure rate**, Multica pauses the autopilot and notifies the creator. Fix the cause, then resume manually.

## Permissions

Any member can create autopilots. Creator + owners/admins can edit/run/delete/manage triggers and add collaborators. Collaborators can edit/run/manage triggers but can't grant access. Managing an autopilot doesn't bypass the agent's **Access**.

## CLI reference

```bash
multica autopilot list/get
multica autopilot create --title "..." --agent <agent> --mode create-issue|run-only [--project --subscriber]
multica autopilot update <id> ...
multica autopilot delete <id>              # archives (keeps history)
multica autopilot trigger <id>             # run now
multica autopilot runs <id>                # run history
multica autopilot trigger-add <id> ...     # schedule or webhook
multica autopilot trigger-update <id> <trigger-id> ...
multica autopilot trigger-delete <id> <trigger-id>
multica autopilot trigger-rotate-url <id> <trigger-id>
```

`autopilot get` nulls `webhook_token`/`webhook_path`/`webhook_url` by default (returns `has_webhook_token` + `webhook_token_hint`); add `--show-secrets` only when you intentionally need the live credential.

## License
MIT
