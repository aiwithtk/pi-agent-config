---
name: multica-runtime
description: How Multica executes runs — the daemon, AI coding tool detection, custom runtime profiles, the task runtime environment, and the security model. Use when a Multica daemon task needs an LLM to execute it, or when configuring runtimes.
---

# multica-runtime

How Multica actually executes runs: the **daemon** on a computer claims runs and invokes an installed **AI coding tool**. This skill covers detection, custom runtime profiles, the injected task environment, and the security model — plus a vendor-agnostic local runtime for LLMs without a native CLI.

## Mental model (official docs)

- **Daemon** = background process on one computer; connects to the server, detects local tools, claims runs, reports results.
- **Runtime** = one computer + one AI coding tool (or one custom runtime profile). One daemon registers one runtime per detected tool per workspace.
- The daemon needs **at least one supported tool detected on `PATH`** before it starts. Restart it after installing a tool (`multica daemon restart`).
- Heartbeat every 15s; an unexpected daemon exit shows the runtime offline within ~3 minutes.
- Concurrency: daemon cap **20** runs, agent cap **6**; effective = smaller of the two.

## Supported AI coding tools (detected command)

`agy` (Antigravity) · `claude` (Claude Code) · `codex` · `codebuddy` · `codearts` · `copilot` · `cursor-agent` · `dsh` (DeepSeek Harness) · `deveco` · `grok` · `hermes` · `kimi` · `kiro-cli` · `mcode` (MiniMax Code) · `openclaw` · `opencode` · `pi` · `omp` (Oh-My-Pi) · `qodercli` / `qoderclicn` · `qwen` · `qwenpaw` · `reasonix` · `traecli` · `dim`

Per-tool differences (session resumption, managed MCP, skill injection path) are in `/docs/providers`. Skill injection paths: `.claude/skills/`, `$CODEX_HOME/skills/`, `.pi/skills/`, `.cursor/skills/`, `.grok/skills/`, etc.

## Daemon commands

```bash
multica daemon start [--foreground] [--device-name] [--runtime-name] [--workspaces-root] [--max-concurrent-tasks]
multica daemon status --output json
multica daemon logs --lines 100 [--follow]
multica daemon restart      # re-detect tools after install
multica daemon stop
multica runtime list
multica runtime rename <id> "Office Mac"
multica runtime usage <id>
multica runtime delete <id> --cascade   # unbinds agents, preserves config, cancels runs
multica config set workspaces_root <path>
multica config show
```

## Custom runtime profiles

A custom profile wraps a compatible command (internal wrapper, version-pinned executable, fixed extra args). It does **not** add a new protocol — you pick an existing **protocol family** (the tool's integration protocol type) and the command must be compatible with it.

- Only workspace owners/admins create/edit/delete profiles.
- The **command field** takes an executable + arguments, **not** a shell script. Quotes/backslash escapes work; pipes/redirects/`&&`/`;`/backticks/env expansion do **not** (put those in a wrapper script).
- Argument order: `<your command> <your fixed args> <Multica protocol args> <agent custom args>`. Multica's own values win conflicts; protocol-critical flags (`-p`, `--output-format`, `--input-format`, `--permission-mode`) are dropped from your fixed args.
- Pin a local executable path per computer: `multica runtime profile set-path <id> --path /abs/path`.

## Task runtime environment (injected by the daemon)

Five variables are the **integration contract** (build on these only):

| Variable | Value |
|---|---|
| `MULTICA_TOKEN` | task-scoped `mat_` API credential (max 24h) |
| `MULTICA_TASK_ID` | ID of the active task |
| `MULTICA_AGENT_ID` | ID of the assigned agent |
| `MULTICA_WORKSPACE_ID` | ID of the task's workspace |
| `MULTICA_SERVER_URL` | server URL selected by the daemon |

Informational (may change): `MULTICA_TASK_CONFIG_ROOT`, `MULTICA_TASK_WORKSPACES_ROOT`, `MULTICA_AGENT_NAME`, `MULTICA_DAEMON_PORT`, `MULTICA_TASK_SLOT`, `TMPDIR` (also `TMP`/`TEMP`).

- These live in the real process env; child processes inherit them (including `MULTICA_TOKEN`). Strip it from children that shouldn't hold it. Never put the token in a prompt, log, or repo.
- Writes made with `MULTICA_TOKEN` are attributed to the agent + task.

## Security model (critical)

- **A run executes with the full permissions of the OS user running the daemon** — it can read SSH keys, edit shell profiles, reach the network. Multica makes **no filesystem-sandbox guarantee**.
- Defaults: Codex runs `sandbox_mode = "danger-full-access"`, Claude Code `--permission-mode bypassPermissions` (unattended).
- Isolation must come from the boundary you put around the daemon: dedicated Unix user → container → VM (lightest to strongest).
- Conveniences that are **not** a boundary: per-run working directory (`~/multica_workspaces/`), per-run agent state (`CODEX_HOME`/`HERMES_HOME`), run-scoped `MULTICA_TOKEN`.
- `custom_env` is stored **server-side** and sent to the runtime — not "stays on this machine".

## Vendor-agnostic local runtime (`multica-llm-runtime`)

For LLMs with no native Multica CLI, this local script reads `input.json`, routes to any backend, and writes `output.json` (see `src/multica-llm-runtime.py` and `docs/README.md`).

| Backend | `--llm` example | Notes |
|---|---|---|
| Ollama | `ollama:llama3` | needs `ollama serve` |
| OpenAI | `openai:gpt-4o` | needs `OPENAI_API_KEY` |
| LiteLLM | `litellm:claude-3-haiku` | needs `LITELLM_API_KEY`/proxy |
| HTTP API | `http://localhost:8000/v1/chat/completions` | OpenAI-compatible |
| Static file | `file:/path/prompt.txt` | file content = system prompt + issue body |
| Raw text | `text:You are a coding assistant.` | inline prompt |

```bash
chmod +x ~/.local/bin/multica-llm-runtime
~/.local/bin/multica-llm-runtime execute MUL-123 --llm ollama:llama3
~/.local/bin/multica-llm-runtime execute MUL-123 --llm text:"You code." --dry-run
```

## Installation
```bash
sudo ln -s ~/.local/bin/multica-llm-runtime /usr/local/bin/multica-llm-runtime
```

## License
MIT
