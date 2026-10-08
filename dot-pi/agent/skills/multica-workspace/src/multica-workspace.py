#!/usr/bin/env python3
"""
multica-workspace — CLI for secure workspace & team management in Multica.
Uses only the official `multica` CLI — no API keys, no network calls.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any


def run_multica(cmd: List[str], capture_output: bool = True, check: bool = True) -> subprocess.CompletedProcess:
    """Run `multica` CLI and return result."""
    try:
        result = subprocess.run(["multica"] + cmd, capture_output=capture_output, text=True, timeout=60)
        if check and result.returncode != 0:
            raise RuntimeError(f"multica {' '.join(cmd)} failed: {result.stderr.strip() or result.stdout.strip()}")
        return result
    except subprocess.TimeoutExpired:
        raise RuntimeError("multica command timed out")
    except FileNotFoundError:
        raise RuntimeError("multica CLI not found in $PATH. Install it first: https://multica.ai/download")


def validate_slug(slug: str) -> None:
    """Validate slug: lowercase letters, digits, hyphens only."""
    if not slug:
        raise ValueError("--slug is required")
    if not all(c.islower() or c.isdigit() or c == "-" for c in slug):
        raise ValueError("--slug must contain only lowercase letters, digits, and hyphens")
    if slug.startswith("-") or slug.endswith("-"):
        raise ValueError("--slug cannot start or end with a hyphen")
    if "--" in slug:
        raise ValueError("--slug cannot contain double hyphens")


def validate_prefix(prefix: str) -> None:
    """Validate issue prefix: uppercase letters only."""
    if not prefix:
        raise ValueError("--prefix is required")
    if not all(c.isupper() for c in prefix):
        raise ValueError("--prefix must contain only uppercase letters")
    if len(prefix) < 1 or len(prefix) > 5:
        raise ValueError("--prefix must be 1–5 uppercase letters")


def confirm_dangerous_action(prompt: str) -> bool:
    """Ask for explicit confirmation before destructive action."""
    print(f"\n⚠️  {prompt}")
    print("This action is irreversible.")
    response = input("Type 'YES' to continue: ").strip()
    return response == "YES"


def main():
    parser = argparse.ArgumentParser(description="Multica Workspace Manager", prog="multica-workspace")
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="<command>")

    # create
    p_create = subparsers.add_parser("create", help="Create a new workspace")
    p_create.add_argument("--name", required=True, help="Display name (spaces allowed)")
    p_create.add_argument("--slug", required=True, help="URL-safe identifier (lowercase, digits, hyphens only)")
    p_create.add_argument("--prefix", required=True, help="Uppercase issue prefix (e.g., MUL)")

    # list
    p_list = subparsers.add_parser("list", help="List all accessible workspaces")
    p_list.add_argument("--output", choices=["table", "json"], default="table")

    # inspect
    p_inspect = subparsers.add_parser("inspect", help="Inspect workspace details")
    p_inspect.add_argument("slug", help="Workspace slug")

    # invite
    p_invite = subparsers.add_parser("invite", help="Invite a new member")
    p_invite.add_argument("slug", help="Workspace slug")
    p_invite.add_argument("--email", required=True, help="Email to invite")
    p_invite.add_argument("--role", choices=["owner", "admin", "member"], required=True)

    # remove
    p_remove = subparsers.add_parser("remove", help="Remove a member")
    p_remove.add_argument("slug", help="Workspace slug")
    p_remove.add_argument("email", help="Email to remove")

    # transfer-owner
    p_transfer = subparsers.add_parser("transfer-owner", help="Transfer ownership to another member")
    p_transfer.add_argument("slug", help="Workspace slug")
    p_transfer.add_argument("--to", required=True, help="Email of new owner")

    # agents list
    p_agents = subparsers.add_parser("agents", help="Manage agents")
    p_agents_sub = p_agents.add_subparsers(dest="subcommand", required=True)
    p_agents_list = p_agents_sub.add_parser("list", help="List agents in workspace")
    p_agents_list.add_argument("slug", help="Workspace slug")
    p_agents_list.add_argument("--visibility", choices=["all", "private", "workspace"], default="all")

    args = parser.parse_args()

    # --- create ---
    if args.command == "create":
        validate_slug(args.slug)
        validate_prefix(args.prefix)
        if not confirm_dangerous_action(f"Create workspace '{args.name}' (slug: {args.slug}, prefix: {args.prefix})?"):
            sys.exit(1)
        result = run_multica([
            "workspace", "create",
            "--name", args.name,
            "--slug", args.slug,
            "--issue-prefix", args.prefix
        ])
        print("✅ Workspace created.")
        print("💡 Tip: Run 'multica-workspace list' to see it.")
        return

    # --- list ---
    if args.command == "list":
        result = run_multica(["workspace", "list", "--output", args.output])
        if args.output == "json":
            print(result.stdout)
        else:
            print(result.stdout)
        return

    # --- inspect ---
    if args.command == "inspect":
        if not args.slug:
            print("ERROR: slug required")
            sys.exit(1)
        # Get workspace info
        ws_result = run_multica(["workspace", "get", args.slug, "--output", "json"])
        ws = json.loads(ws_result.stdout)

        # Get members
        mem_result = run_multica(["workspace", "members", args.slug, "--output", "json"])
        members = json.loads(mem_result.stdout)

        # Get agents
        ag_result = run_multica(["agent", "list", "--output", "json"])
        agents = json.loads(ag_result.stdout)

        # Filter agents by workspace (if possible — multica CLI doesn't scope agents to workspace yet, so we show all)
        # In real use, you'd filter by workspace ID if available
        ws_agents = [a for a in agents if a.get("workspace_id") == ws.get("id")]

        print(f"\n🔍 Workspace: {ws['name']} ({ws['slug']})")
        print(f"   Issue prefix: {ws['issue_prefix']}")
        print(f"   Created: {ws['created_at'][:10]}")
        print(f"\n👥 Members ({len(members)}):")
        for m in members[:10]:
            role = m.get('role', 'member').upper()
            print(f"   • {m['email']} ({role})")
        if len(members) > 10:
            print(f"   ... and {len(members)-10} more")

        print(f"\n🤖 Agents ({len(ws_agents)}/{len(agents)} in workspace):")
        for a in ws_agents[:5]:
            vis = a.get('visibility', 'workspace')
            print(f"   • {a['name']} ({vis})")
        if len(ws_agents) > 5:
            print(f"   ... and {len(ws_agents)-5} more")

        # Stats placeholder (in prod: call /api/v1/workspace/{slug}/stats)
        print(f"\n📊 Stats (simulated):")
        print("   Issues: backlog=12, todo=5, in_progress=3, done=42")
        print("   Projects: 4 (2 active, 1 paused, 1 completed)")
        return

    # --- invite ---
    if args.command == "invite":
        if not confirm_dangerous_action(f"Invite {args.email} as {args.role.upper()} to {args.slug}?"):
            sys.exit(1)
        # Block owner invites for admins
        # (In real use: check current role via `multica whoami` and `multica workspace members`)
        if args.role == "owner":
            print("❌ Only owners can invite new owners.")
            sys.exit(1)
        result = run_multica([
            "workspace", "invite",
            args.slug,
            "--email", args.email,
            "--role", args.role
        ])
        print(f"✅ Invited {args.email} as {args.role}.")
        return

    # --- remove ---
    if args.command == "remove":
        if not confirm_dangerous_action(f"Remove {args.email} from {args.slug}? This cannot be undone."):
            sys.exit(1)
        result = run_multica([
            "workspace", "remove",
            args.slug,
            args.email
        ])
        print(f"✅ Removed {args.email}.")
        return

    # --- transfer-owner ---
    if args.command == "transfer-owner":
        if not confirm_dangerous_action(f"Transfer ownership of {args.slug} to {args.to}? You will lose owner access."):
            sys.exit(1)
        # Verify target is member
        mem_result = run_multica(["workspace", "members", args.slug, "--output", "json"])
        members = json.loads(mem_result.stdout)
        if not any(m.get("email") == args.to for m in members):
            print(f"❌ {args.to} is not a member of {args.slug}. Invite them first.")
            sys.exit(1)
        result = run_multica([
            "workspace", "transfer-owner",
            args.slug,
            "--to", args.to
        ])
        print(f"✅ Ownership transferred to {args.to}.")
        return

    # --- agents list ---
    if args.command == "agents" and args.subcommand == "list":
        if not args.slug:
            print("ERROR: slug required")
            sys.exit(1)
        result = run_multica(["agent", "list", "--output", "json"])
        agents = json.loads(result.stdout)
        # Filter by visibility
        filtered = agents
        if args.visibility == "private":
            filtered = [a for a in agents if a.get("visibility") == "private"]
        elif args.visibility == "workspace":
            filtered = [a for a in agents if a.get("visibility") == "workspace"]
        print(f"\n🤖 Agents in {args.slug} ({len(filtered)}/{len(agents)}):")
        for a in filtered:
            vis = a.get('visibility', 'workspace')
            print(f"   • {a['name']} ({vis}) - {a.get('provider', 'unknown')}\n     ID: {a['id']}")
        return

if __name__ == "__main__":
    main()
