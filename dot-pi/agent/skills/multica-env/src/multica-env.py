#!/usr/bin/env python3
"""
multica-env — CLI for auditing and securing self-hosted Multica server environments.
Validates .env files, detects silent fallbacks, scans for security risks, and simulates allowlist logic.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any


def load_env_file(path: str) -> Dict[str, str]:
    """Load .env file into dict."""
    env = {}
    if not os.path.exists(path):
        return env
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"): continue
            if "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip("'\"")
    return env


def run_command(cmd: List[str], capture_output: bool = True) -> subprocess.CompletedProcess:
    """Run command and return result."""
    try:
        return subprocess.run(cmd, capture_output=capture_output, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Command timed out: {' '.join(cmd)}")
    except Exception as e:
        raise RuntimeError(f"Command failed: {' '.join(cmd)} — {e}")


def check_production_vars(env: Dict[str, str]) -> List[str]:
    """Check required production variables."""
    required = ["JWT_SECRET", "APP_ENV", "FRONTEND_ORIGIN", "DATABASE_URL"]
    missing = []
    issues = []
    for var in required:
        if not env.get(var):
            missing.append(var)
    if missing:
        issues.append(f"❌ Missing required vars: {', '.join(missing)}")
    
    # JWT_SECRET safety
    jwt = env.get("JWT_SECRET", "")
    if jwt == "multica-dev-secret-change-in-production":
        issues.append("❌ JWT_SECRET uses default value → HIGH RISK")
    elif len(jwt) < 32:
        issues.append(f"⚠️  JWT_SECRET is {len(jwt)} chars → RECOMMEND 32+ (current: '{jwt[:10]}...')")
    
    # APP_ENV
    if env.get("APP_ENV") != "production":
        issues.append(f"⚠️  APP_ENV is '{env.get('APP_ENV')}' → must be 'production' in prod")
    
    # FRONTEND_ORIGIN
    origin = env.get("FRONTEND_ORIGIN", "")
    if not origin.startswith(("http://", "https://")):
        issues.append(f"❌ FRONTEND_ORIGIN must start with http:// or https:// (got '{origin}')")
    elif "localhost" in origin or ".local" in origin or re.match(r"https?://\d+\.\d+\.\d+\.\d+", origin):
        issues.append(f"⚠️  FRONTEND_ORIGIN uses localhost/IP → may break invite links & WebSocket")
    
    return issues


def audit_silent_fallbacks(env: Dict[str, str]) -> List[str]:
    """Detect variables that cause silent failures."""
    issues = []
    if not env.get("RESEND_API_KEY"):
        issues.append("⚠️  RESEND_API_KEY not set → emails go to stdout only")
    if not env.get("S3_BUCKET"):
        issues.append("⚠️  S3_BUCKET not set → uploads fall back to local disk")
    if not env.get("CLOUDFRONT_DOMAIN") and env.get("S3_BUCKET"):
        issues.append("⚠️  CLOUDFRONT_DOMAIN not set → CDN disabled (S3 enabled)")
    return issues


def security_scan(env: Dict[str, str], detect_secrets: bool = False) -> List[str]:
    """Scan for security risks."""
    issues = []
    
    # MULTICA_DEV_VERIFICATION_CODE in prod
    dev_code = env.get("MULTICA_DEV_VERIFICATION_CODE")
    app_env = env.get("APP_ENV")
    if dev_code and app_env == "production":
        issues.append("❌ MULTICA_DEV_VERIFICATION_CODE set in production → CRITICAL")
    
    # Exposed secrets in .env
    if detect_secrets:
        secret_patterns = [
            r"^(PAT|TOKEN|API_KEY|SECRET|PASSWORD|KEY)=",
            r"(mul_|mdt_)\w{10,}",
        ]
        for k, v in env.items():
            for pattern in secret_patterns:
                if re.search(pattern, k) or re.search(pattern, v):
                    issues.append(f"❌ Secret-like var found: {k}={v[:15]}... → NEVER store tokens in .env")
                    break
    
    return issues


def simulate_signup(env: Dict[str, str], email: str) -> str:
    """Simulate signup allowlist logic (AND semantics)."""
    if not email:
        return "❌ --simulate-email required"
    
    allowed_emails = [e.strip() for e in env.get("ALLOWED_EMAILS", "").split(",") if e.strip()]
    allowed_domains = [d.strip() for d in env.get("ALLOWED_EMAIL_DOMAINS", "").split(",") if d.strip()]
    allow_signup = env.get("ALLOW_SIGNUP", "true").lower() == "true"
    
    # If any allowlist is non-empty, all must match
    if allowed_emails or allowed_domains:
        # Check email
        if allowed_emails and email not in allowed_emails:
            return f"❌ {email} not in ALLOWED_EMAILS"
        # Check domain
        if allowed_domains:
            domain = email.split("@", 1)[-1] if "@" in email else ""
            if domain not in allowed_domains:
                return f"❌ {domain} not in ALLOWED_EMAIL_DOMAINS"
        # Allow signup must be true
        if not allow_signup:
            return f"❌ ALLOW_SIGNUP=false blocks all signups"
        return f"✅ {email} is allowed"
    
    # No allowlist → open signup
    return f"✅ {email} is allowed (no allowlist configured)"


def diagnose_port(port: str) -> List[str]:
    """Check if port is free."""
    issues = []
    try:
        if os.name == "nt":  # Windows
            r = run_command(["netstat", "-ano", "|", "findstr", f":{port}"], capture_output=False)
            if r.returncode == 0:
                issues.append(f"❌ Port {port} is in use")
            else:
                issues.append(f"✅ Port {port} is free")
        else:  # macOS/Linux
            r = run_command(["lsof", "-i", f":{port}"], capture_output=False)
            if r.returncode == 0:
                issues.append(f"❌ Port {port} is in use")
            else:
                issues.append(f"✅ Port {port} is free")
    except Exception as e:
        issues.append(f"⚠️  Port check failed: {e}")
    return issues


def validate_oauth(env: Dict[str, str]) -> List[str]:
    """Validate OAuth config."""
    issues = []
    redirect = env.get("GOOGLE_REDIRECT_URI", "")
    origin = env.get("FRONTEND_ORIGIN", "")
    if redirect and origin:
        expected = origin.rstrip("/") + "/auth/callback"
        if redirect != expected:
            issues.append(f"❌ GOOGLE_REDIRECT_URI='{redirect}' → should be '{expected}'")
    return issues


def main():
    parser = argparse.ArgumentParser(description="Multica Environment Auditor", prog="multica-env")
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="<command>")

    # check
    p_check = subparsers.add_parser("check", help="Validate required production variables")
    p_check.add_argument("--env", choices=["production", "staging", "development"], default="production", help="Environment type")
    p_check.add_argument("--file", default=".env", help="Path to .env file")

    # audit
    p_audit = subparsers.add_parser("audit", help="Audit for silent fallbacks and risky defaults")
    p_audit.add_argument("--file", default=".env", help="Path to .env file")
    p_audit.add_argument("--include-daemon-status", action="store_true", help="Read multica daemon status (if CLI installed)")
    p_audit.add_argument("--include-desktop-config", action="store_true", help="Check ~/.multica/desktop.json")

    # security-scan
    p_sec = subparsers.add_parser("security-scan", help="Scan for security risks")
    p_sec.add_argument("--file", default=".env", help="Path to .env file")
    p_sec.add_argument("--detect-secrets", action="store_true", help="Scan for exposed PAT/TOKEN/KEY in .env")

    # validate
    p_val = subparsers.add_parser("validate", help="Validate signup logic")
    p_val.add_argument("--simulate-email", help="Email to simulate")
    p_val.add_argument("--file", default=".env", help="Path to .env file")

    # diff
    p_diff = subparsers.add_parser("diff", help="Compare two .env files")
    p_diff.add_argument("file1", help="First .env file")
    p_diff.add_argument("file2", help="Second .env file")

    # diagnose-port
    p_port = subparsers.add_parser("diagnose-port", help="Check if port is free")
    p_port.add_argument("port", help="Port number to check")

    args = parser.parse_args()

    # Load env
    env = load_env_file(args.file) if hasattr(args, "file") else {}

    # --- check ---
    if args.command == "check":
        issues = check_production_vars(env)
        if issues:
            print("\n🔍 Production validation issues:")
            for i in issues:
                print(i)
        else:
            print("✅ All production variables OK.")
        return

    # --- audit ---
    if args.command == "audit":
        issues = audit_silent_fallbacks(env)
        issues += validate_oauth(env)
        if args.include_daemon_status:
            try:
                r = run_command(["multica", "daemon", "status", "--output", "json"])
                if r.returncode == 0:
                    print("✅ Daemon status read successfully.")
                else:
                    issues.append("⚠️  Failed to read daemon status")
            except Exception as e:
                issues.append(f"⚠️  Daemon status check failed: {e}")
        if args.include_desktop_config:
            desktop_cfg = Path("~/.multica/desktop.json").expanduser()
            if desktop_cfg.exists():
                try:
                    with open(desktop_cfg) as f:
                        json.load(f)
                    print("✅ Desktop config (~/.multica/desktop.json) is valid.")
                except Exception as e:
                    issues.append(f"❌ Desktop config invalid: {e}")
            else:
                issues.append("⚠️  Desktop config (~/.multica/desktop.json) not found")
        if issues:
            print("\n🔍 Audit findings:")
            for i in issues:
                print(i)
        else:
            print("✅ No audit issues found.")
        return

    # --- security-scan ---
    if args.command == "security-scan":
        issues = security_scan(env, args.detect_secrets)
        if issues:
            print("\n🔒 Security scan results:")
            for i in issues:
                print(i)
        else:
            print("✅ No security issues found.")
        return

    # --- validate ---
    if args.command == "validate":
        if not args.simulate_email:
            print("ERROR: --simulate-email required")
            sys.exit(1)
        result = simulate_signup(env, args.simulate_email)
        print(result)
        return

    # --- diff ---
    if args.command == "diff":
        env1 = load_env_file(args.file1)
        env2 = load_env_file(args.file2)
        keys = sorted(set(env1.keys()) | set(env2.keys()))
        print(f"\n📋 Diff {args.file1} ↔ {args.file2}:")
        for k in keys:
            v1 = env1.get(k, "[not set]")
            v2 = env2.get(k, "[not set]")
            if v1 != v2:
                print(f"  {k}: {v1!r} → {v2!r}")
        return

    # --- diagnose-port ---
    if args.command == "diagnose-port":
        issues = diagnose_port(args.port)
        for i in issues:
            print(i)
        return

if __name__ == "__main__":
    main()
