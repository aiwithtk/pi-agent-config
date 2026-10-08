# Critical Security Risks

⚠️ These are the top risks detected by `multica-env security-scan`:

## 1. `MULTICA_DEV_VERIFICATION_CODE` in production
- Setting this variable in production allows anyone who can request a verification code to sign in with that fixed value.
- It is ignored when `APP_ENV=production`, but if set *and* `APP_ENV` is misconfigured, it creates a critical vulnerability.
- ✅ Fix: Remove `MULTICA_DEV_VERIFICATION_CODE` from `.env` in production.

## 2. Weak `JWT_SECRET`
- Default value `multica-dev-secret-change-in-production` is unsafe and must never be used.
- Short secrets (< 32 chars) are vulnerable to brute-force attacks.
- ✅ Fix: Generate a cryptographically secure 32+ char string (e.g., `openssl rand -hex 32`).

## 3. Secrets exposed in `.env`
- Storing `PAT=...`, `TOKEN=...`, or `API_KEY=...` in `.env` exposes credentials to any process reading the file.
- Multica stores only the hash of PATs — they should never appear in `.env`.
- ✅ Fix: Use environment injection at runtime (e.g., Docker secrets, Kubernetes secrets, vault) — never hardcode tokens.

🔐 This tool prioritizes defense-in-depth — because one misconfigured env var can compromise your entire deployment.
