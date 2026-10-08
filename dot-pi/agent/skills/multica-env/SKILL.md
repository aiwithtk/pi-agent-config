---
name: multica-env
description: Ops-first CLI for auditing, validating, and securing self-hosted Multica server environments — detects missing env vars, silent fallbacks, security risks, and misconfigurations. Use for Multica server operations.
---

# multica-env

An ops-first CLI for auditing, validating, and securing self-hosted Multica server environments — detects missing variables, silent fallbacks, security risks, and misconfigurations before they break production.

## Overview
`multica-env` reads your `.env` (or environment) and validates it against Multica's production requirements. It surfaces risks that cause silent failures — emails going to the log instead of users, uploads falling back to local disk, or WebSocket origin mismatches.

It covers:
- ✅ Audit of critical vars (`JWT_SECRET`, `APP_ENV`, `FRONTEND_ORIGIN`, `DATABASE_URL`)
- ✅ Detection of "silent fallback" vars (`RESEND_API_KEY`, `S3_BUCKET`, `REDIS_URL`)
- ✅ Security scanning (weak `JWT_SECRET`, `MULTICA_DEV_VERIFICATION_CODE` in prod, leaked PATs)
- ✅ Signup allowlist simulation (`--simulate-email user@domain.com`)
- ✅ Port diagnostics (`--diagnose-port 8080`) and OAuth validation

## Reference (current docs — `/docs/environment-variables`)

### Core (required in production)
| Var | Default | Notes |
|---|---|---|
| `DATABASE_URL` | local `multica` DB | PostgreSQL connection string |
| `JWT_SECRET` | **required** | gen: `openssl rand -hex 32`; prod refuses to boot on empty/placeholder |
| `APP_ENV` | empty | set `production` in prod |
| `FRONTEND_ORIGIN` | empty | frontend origin (CORS, cookies, invite links); required for self-host |
| `MULTICA_APP_URL` | falls back to `FRONTEND_ORIGIN` | user-reachable web URL (CLI sign-in, account links) |
| `MULTICA_PUBLIC_URL` | empty | public API URL (webhook URLs, runtime instructions) |
| `MULTICA_DAEMON_SERVER_URL` | falls back to `MULTICA_PUBLIC_URL` → app → frontend | URL daemons use to reach the API |

- `AUTH_TOKEN_TTL` (default `720h` = 30 days) — sessions slide; min `60s`.
- `COOKIE_DOMAIN` — required only when frontend and API use different hosts and the browser talks to the API domain directly (else 403 CSRF). Never an IP.
- `MULTICA_RUNTIME_RECONNECT_GRACE` (default `3h`) — how long an offline runtime may reconnect before in-flight runs fail.

### Email (verification codes / invitations)
- `RESEND_API_KEY` + `RESEND_FROM_EMAIL` (verified domain) — or —
- `SMTP_HOST` + `SMTP_PORT`/`SMTP_USERNAME`/`SMTP_PASSWORD`/`SMTP_FROM_EMAIL` (`SMTP_HOST` wins over Resend).
- No email service ⇒ codes/invites only in the **backend log** (DEV mode). Fine for dev, not prod.
- `MULTICA_DEV_VERIFICATION_CODE` (6 digits) — ignored when `APP_ENV=production`; never enable publicly.

### Google OAuth
`GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / `GOOGLE_REDIRECT_URI` (must match console exactly).

### Signup scope
- `ALLOW_SIGNUP` (default `true`), `ALLOWED_EMAILS`, `ALLOWED_EMAIL_DOMAINS`, `DISABLE_WORKSPACE_CREATION`.
- Evaluation order: exact email → domain → no allowlist + `ALLOW_SIGNUP` → pending invitation → reject.

### Storage
- `S3_BUCKET` / `S3_REGION` / `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_ENDPOINT_URL` (MinIO) / `S3_USE_PATH_STYLE`.
- `ATTACHMENT_DOWNLOAD_MODE` (`auto`/`cloudfront`/`presign`/`proxy`) — use `proxy` when the bucket isn't browser-reachable.
- `LOCAL_UPLOAD_DIR` (default `./data/uploads`, needs a persistent volume) — used when `S3_BUCKET` unset.

### Redis / rate limiting
- `REDIS_URL` — one URL for all Redis-backed features (rate limiting, realtime, channel WebSocket leases, token caches).
- `REDIS_CLUSTER_MODE`, `RATE_LIMIT_AUTH` (5/min), `RATE_LIMIT_AUTH_VERIFY` (20/min), invitation rate limits, `RATE_LIMIT_TRUSTED_PROXIES` / `MULTICA_TRUSTED_PROXIES`.
- Auth rate limits require `REDIS_URL`; without it they are disabled.

### Integrations (self-host)
`GITHUB_APP_SLUG`, `GITHUB_WEBHOOK_SECRET`, `GITHUB_APP_ID`, `GITHUB_APP_PRIVATE_KEY` · `COMPOSIO_API_KEY` · `MULTICA_VCS_INTEGRATION_ENABLED` + `MULTICA_VCS_SECRET_KEY` (Forgejo/Gitea/GitLab) · `MULTICA_LARK_SECRET_KEY` / `MULTICA_SLACK_SECRET_KEY` / `MULTICA_DINGTALK_SECRET_KEY` / `MULTICA_WECOM_SECRET_KEY` / `MULTICA_TELEGRAM_SECRET_KEY` (each a base64 32-byte key, `openssl rand -base64 32`) · `MULTICA_PLUGIN_*`.

### Daemon-side (read on the computer that runs agents)
`MULTICA_SERVER_URL` · `MULTICA_DAEMON_MAX_CONCURRENT_TASKS` (20) · `MULTICA_AGENT_TIMEOUT` (0 = none) · `MULTICA_DAEMON_HEARTBEAT_INTERVAL` (15s) · `MULTICA_DAEMON_POLL_INTERVAL` (30s) · `MULTICA_WORKSPACES_ROOT` (`~/multica_workspaces`) · `MULTICA_<PROVIDER>_PATH` / `MULTICA_<PROVIDER>_MODEL` / `MULTICA_<PROVIDER>_ARGS` · `DO_NOT_TRACK` / `ANALYTICS_DISABLED` / `METRICS_ADDR`.

## Deployment notes (self-host quickstart)
- `make selfhost` creates `.env` (generates `JWT_SECRET`, Postgres password, `MULTICA_VCS_SECRET_KEY`), pulls images, starts 3 containers (`postgres`, `backend`, `frontend`). Re-running reuses `.env`/volumes.
- Containers read `.env` only at creation: `docker compose -f docker-compose.selfhost.yml up -d` re-reads it; `docker compose restart` does **not**.
- Verify with `/readyz` (`{"status":"ok","checks":{"db":"ok","migrations":"ok"}}`), not `/health` (liveness only).
- Migrations run automatically on backend startup — no manual migration command.
- Back up Postgres before upgrade: `pg_dump ... > backup.sql && gzip backup.sql` (don't pipe directly into gzip).

## Commands

### `multica-env check --env production`
```bash
multica-env check --env production
```
❌ `JWT_SECRET` uses default/placeholder → HIGH RISK
✅ `FRONTEND_ORIGIN` set to https://multica.example.com

### `multica-env audit`
```bash
multica-env audit
```
⚠️ `RESEND_API_KEY` / `SMTP_HOST` not set → codes only in log
⚠️ `S3_BUCKET` not set → uploads fall back to local disk
⚠️ `REDIS_URL` not set → auth rate limiting disabled

### `multica-env security-scan [--detect-secrets]`
```bash
multica-env security-scan --detect-secrets
```
❌ `PAT=mul_abc123` in .env → CRITICAL
❌ `MULTICA_DEV_VERIFICATION_CODE=888888` + `APP_ENV=production` → CRITICAL

### `multica-env validate --simulate-email admin@mycorp.com`
Simulates the signup allowlist (AND semantics: email → domain → allowlist/ALLOW_SIGNUP → invitation).

### `multica-env diagnose-port 8080`
Checks if a port is free (`lsof` on macOS/Linux, `netstat` on Windows).

### `multica-env diff <file1.env> <file2.env>`
Compares two env files (staging vs prod).

## Safety guarantees
- 🔒 `security-scan` blocks execution if `MULTICA_DEV_VERIFICATION_CODE` is set in production.
- 🛑 `check` refuses to proceed without `JWT_SECRET`, `APP_ENV`, `FRONTEND_ORIGIN`, `DATABASE_URL`.
- ⚠️ `audit` highlights every fallback that causes silent failure.
- 🧯 `--pre-setup` warns before running `multica setup self-host`.

## Installation
```bash
chmod +x ~/.local/bin/multica-env
sudo ln -s ~/.local/bin/multica-env /usr/local/bin/multica-env
```

## License
MIT
