---
name: multica-daemon
description: Operate the Multica daemon and runtimes, and understand run states, retries, and failures — start/stop/status/logs, runtime management, run lifecycle, and troubleshooting. Use for Multica execution and ops.
---

# multica-daemon

Operational reference for the **daemon**, **runtimes**, and the **run lifecycle** (states, retries, failures) plus troubleshooting. For the execution model, custom runtime profiles, task env vars, and the security model, see the `multica-runtime` skill.

## Daemon lifecycle

```bash
multica daemon start [--foreground] [--device-name] [--runtime-name] [--workspaces-root] [--max-concurrent-tasks]
multica daemon status --output json
multica daemon logs --lines 100 [--follow]
multica daemon restart      # re-detect tools after install/sign-in
multica daemon stop
multica daemon disk-usage [--by-workspace --by-task --top]
```

- The daemon connects to the server, detects tools on `PATH`, claims runs, reports results. Needs ≥1 supported tool before it starts.
- Heartbeat every **15s**; after an unexpected exit the runtime shows offline within ~3 min.
- Daemon logs: `multica daemon logs` prints the absolute path it resolved (default profile `~/.multica/daemon.log`, `daemon.err.log`; named profiles under `~/.multica/profiles/<name>/`).
- Concurrency: daemon cap **20** runs, agent cap **6**; effective = smaller. Config: `MULTICA_DAEMON_MAX_CONCURRENT_TASKS`, or `multica config set max_concurrent_tasks 20`.

## Runtimes

```bash
multica runtime list
multica runtime rename <id> "Office Mac"
multica runtime usage <id>
multica runtime activity <id>
multica runtime update <id> ...
multica runtime delete <id> --cascade   # unbinds agents, preserves config/history, cancels runs
multica runtime profile list/create/update/delete
multica runtime profile set-path <id> --path /abs/path     # local only, never uploaded
multica runtime profile unset-path <id>
```

- A local runtime is **private by default** — only its owner can create agents on it. Only the owner can make it **public**. Admins can rename/delete, but not share.
- A runtime offline > **7 days** with no agents bound (incl. archived) is auto-cleaned.
- `runtime delete` without `--cascade` is refused if active agents are bound.

## Run lifecycle (states)

`deferred` → `queued` → `dispatched` → `waiting_local_directory` → `running` → `completed` | `failed` | `cancelled`

| State | Meaning / timeout |
|---|---|
| `deferred` | scheduled later; enters `queued` at the appointed time |
| `queued` | waiting for a runtime; waits while its runtime heartbeats, plus ≥1 reconnect grace; fails only when both windows pass |
| `dispatched` | claimed, tool starting; treated as failed after > **5 min** |
| `waiting_local_directory` | directory held by another run; no timeout, resumes when released |
| `running` | executing; no fixed cap — liveness follows the heartbeat |

- A queued run is **bound to its runtime** and never moves to another machine.
- `completed` ≠ issue done; it only means that one run ended.
- A run completing does not by itself change issue status (agents write status explicitly).

## Retries

- Auto-retry covers only transient faults: runtime offline, reclaimed after daemon restart, platform execution timeout, Codex stalled, skill-bundle download failure — **2 attempts** by default (first run + 1). Tool network interruptions: up to **3**, final attempt after ~5s delay.
- Auth/quota/config/model errors never auto-retry — fix the cause, then retry manually.
- Retry keeps the previous run's files and (if the session is safe) resumes the session. Poisoned sessions (context overflow) start a fresh session on the original working dir.
- A retry invokes **the agent that handled that run at the time**, even if the issue was reassigned. `multica issue rerun` instead uses the current assignee with a fresh session.

## Failure reasons

**Platform** (`runtime_offline`, `queued_expired`, `runtime_recovery`, `environment_prepare_failed`, `cancelled`, `timeout`, `iteration_limit`, `agent_blocked`, `api_invalid_request`, `codex_semantic_inactivity`).

**Tool side (`agent_error.*`)** — `provider_auth_or_access`, `provider_quota_limit`, `provider_capacity_or_rate_limit`, `provider_server_error`, `provider_network`, `model_not_found_or_unavailable`, `context_overflow`, `missing_config`, `runtime_missing_executable`, `runtime_version_unsupported`, `process_failure`, `empty_or_unparseable_output`, `agent_timeout`, `unknown`.

## Troubleshooting (first commands)

```bash
multica version
multica auth status
multica daemon status --output json
multica daemon logs --lines 100
# self-host:
curl -i https://api.example.com/health    # liveness only
curl -i https://api.example.com/readyz    # db + migrations
```

- **Run stuck `queued`**: check (1) runtime online? (2) tool detected? (3) agent concurrency headroom? (4) daemon capacity?
- **`waiting_local_directory`**: another run uses the same local dir (`in_place` mode); switch to `worktree` for concurrency, or stop the blocking run.
- **Tool online but runs fail**: run the tool directly in a terminal on that machine, check sign-in/API key/quota/model.
- **No live updates**: WebSocket not connected — daemons dial `/api/daemon/ws` (not `/ws`); a bare `curl /ws` returning 400 is expected.
- **`setup self-host` "server not reachable"**: the CLI probes `<server-url>/health` (needs a 200); route `/health` to the backend explicitly.
- **TLS handshake timeout** (Windows/VPN): retry with `GODEBUG=tlsmlkem=0` — some middleboxes drop Go's post-quantum ClientHello.
- **Ports**: API `8080`, web `3000`. `lsof -nP -iTCP:8080 -sTCP:LISTEN`.

## License
MIT
