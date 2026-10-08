# Runtimes: How Agents Execute

A runtime = one **computer + one AI coding tool** (or one custom runtime profile). One daemon registers one runtime per detected tool per workspace.

## Daemon lifecycle

- The daemon detects supported tools on `PATH` at startup. It needs **at least one** supported tool before it starts. Restart after installing a tool: `multica daemon restart`.
- Heartbeat every **15s**. After an unexpected daemon exit, the runtime shows offline within ~**3 minutes** at the latest.
- Concurrency: daemon cap **20** runs, agent cap **6**; effective = the smaller of the two.
- A local runtime is **private by default** — only its owner can create agents on it. Only the owner can make it **public**. Workspace admins can rename/delete a runtime, but not share it.

## Runtime status

| Status | Meaning |
|--------|---------|
| `online` | daemon heartbeating |
| `offline` | heartbeat lost (≈3 min after exit); queued runs wait through the reconnect grace (`MULTICA_RUNTIME_RECONNECT_GRACE`, default 3h) |
| cleaned up | offline > **7 days** with no agents bound (including archived) → auto-removed |

## Supported AI coding tools (detected command)

`agy`, `claude`, `codex`, `codebuddy`, `codearts`, `copilot`, `cursor-agent`, `dsh`, `deveco`, `grok`, `hermes`, `kimi`, `kiro-cli`, `mcode`, `openclaw`, `opencode`, `pi`, `omp`, `qodercli`, `qoderclicn`, `qwen`, `qwenpaw`, `reasonix`, `traecli`, `dim`

## Tool support matrix (key capabilities)

| Tool | Session resumption | Multica-managed MCP | Skill injection path |
|------|--------------------|---------------------|----------------------|
| Antigravity (`agy`) | ✅ | — | `.agents/skills/` |
| Claude Code (`claude`) | ✅ | ✅ | `.claude/skills/` |
| Codex (`codex`) | ✅ | ✅ | `$CODEX_HOME/skills/` |
| GitHub Copilot CLI (`copilot`) | ✅ | — | `.github/skills/` |
| Cursor Agent (`cursor-agent`) | ✅ | ✅ | `.cursor/skills/` |
| Grok (`grok`) | ✅ | ✅ | `.grok/skills/` |
| Hermes (`hermes`) | ✅ | ✅ | per-run `HERMES_HOME/skills/` |
| Pi (`pi`) | ✅ | — | `.pi/skills/` |
| MiniMax Code (`mcode`) | — | ✅ | `.minimax/skills/` |

> Note: "Multica-managed MCP" means MCP servers can be defined in agent config and passed to the tool. Antigravity, Copilot, DevEco Code, and Pi do **not** read the agent's MCP config yet.

Full matrix in the official `/docs/providers`.
