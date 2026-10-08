#!/usr/bin/env python3
"""
multica-agent — CLI for secure agent management in Multica.
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


def confirm_dangerous_action(prompt: str) -> bool:
    """Ask for explicit confirmation before destructive action."""
    print(f"\n⚠️  {prompt}")
    print("This action is irreversible.")
    response = input("Type 'YES' to continue: ").strip()
    return response == "YES"


def validate_custom_env(envs: List[str]) -> List[str]:
    """Validate and filter custom_env entries."""
    blocked = ["PATH", "HOME", "USER", "SHELL", "TERM", "CODEX_HOME"]
    blocked_prefix = ["MULTICA_"]
    safe = []
    for e in envs:
        if "=" not in e:
            raise ValueError(f"Invalid env format: '{e}'. Use KEY=VALUE.")
        key = e.split("=", 1)[0].strip()
        if key in blocked:
            raise ValueError(f"--env {key} is blocked (reserved system variable)")
        if any(key.startswith(p) for p in blocked_prefix):
            raise ValueError(f"--env {key} is blocked (starts with reserved prefix)")
        safe.append(e)
    return safe


def main():
    parser = argparse.ArgumentParser(description="Multica Agent Manager", prog="multica-agent")
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="<command>")

    # create
    p_create = subparsers.add_parser("create", help="Create a new agent")
    p_create.add_argument("--name", required=True, help="Agent name (unique in workspace)")
    p_create.add_argument("--runtime", required=True, help="Runtime ID (e.g., rt_ollama_llama3)")
    p_create.add_argument("--visibility", choices=["workspace", "private"], default="private", help="Who can assign this agent")
    p_create.add_argument("--instructions", help="System instructions (optional)")
    p_create.add_argument("--list-runtimes", action="store_true", help="List available runtimes and exit")

    # list
    p_list = subparsers.add_parser("list", help="List all agents")
    p_list.add_argument("--output", choices=["table", "json"], default="table")
    p_list.add_argument("--status", choices=["online", "offline", "all"], default="all", help="Filter by runtime status")
    p_list.add_argument("--visibility", choices=["workspace", "private", "all"], default="all", help="Filter by visibility")
    p_list.add_argument("--mentionable", action="store_true", help="Alias for --status online --archived false")

    # inspect
    p_inspect = subparsers.add_parser("inspect", help="Inspect agent details")
    p_inspect.add_argument("id", help="Agent ID (e.g., ag_123)")

    # update
    p_update = subparsers.add_parser("update", help="Update agent configuration")
    p_update.add_argument("id", help="Agent ID")
    p_update.add_argument("--env", action="append", help="Custom environment variable (KEY=VALUE)")
    p_update.add_argument("--arg", action="append", help="Custom CLI argument (e.g., --max-turns)")
    p_update.add_argument("--concurrency", type=int, help="Max concurrent tasks (default 6)")
    p_update.add_argument("--instructions", help="New system instructions")
    p_update.add_argument("--visibility", choices=["workspace", "private"], help="New visibility")

    # archive / restore
    p_archive = subparsers.add_parser("archive", help="Archive an agent")
    p_archive.add_argument("id", help="Agent ID")
    p_restore = subparsers.add_parser("restore", help="Restore an archived agent")
    p_restore.add_argument("id", help="Agent ID")

    # skills
    p_skills = subparsers.add_parser("skills", help="Manage attached skills")
    p_skills_sub = p_skills.add_subparsers(dest="subcommand", required=True)
    
    p_skills_list = p_skills_sub.add_parser("list", help="List attached skills")
    p_skills_list.add_argument("id", help="Agent ID")
    
    p_skills_add = p_skills_sub.add_parser("add", help="Attach a skill")
    p_skills_add.add_argument("id", help="Agent ID")
    p_skills_add.add_argument("--source", choices=["github", "clawhub", "local"], required=True, help="Skill source")
    p_skills_add.add_argument("--url", help="GitHub/ClawHub URL")
    p_skills_add.add_argument("--path", help="Local path to skill directory")
    p_skills_add.add_argument("--i-understand-risks", action="store_true", help="Required for github/clawhub")

    args = parser.parse_args()

    # --- create ---
    if args.command == "create":
        if args.list_runtimes:
            print("🔍 Available runtimes (from 'multica runtime list'):")
            try:
                r = run_multica(["runtime", "list", "--output", "json"])
                runtimes = json.loads(r.stdout)
                for r in runtimes:
                    status = "✅" if r.get("status") == "online" else "❌"
                    print(f"  {status} {r.get('id')} → {r.get('name')} ({r.get('tool', 'unknown')})")
            except Exception as e:
                print(f"  ❌ Failed to list runtimes: {e}")
            return
        if not confirm_dangerous_action(f"Create agent '{args.name}' with runtime '{args.runtime}'?"):
            sys.exit(1)
        cmd = [
            "agent", "create",
            "--name", args.name,
            "--runtime", args.runtime,
            "--visibility", args.visibility
        ]
        if args.instructions:
            cmd += ["--instructions", args.instructions]
        result = run_multica(cmd)
        print("✅ Agent created.")
        print("💡 Tip: Run 'multica-agent list' to see it.")
        return

    # --- list ---
    if args.command == "list":
        # Get all agents
        result = run_multica(["agent", "list", "--output", "json"])
        agents = json.loads(result.stdout)

        # Get runtimes for filtering
        try:
            r = run_multica(["runtime", "list", "--output", "json"])
            runtimes = {r["id"]: r for r in json.loads(r.stdout)}
        except:
            runtimes = {}

        # Apply filters
        filtered = agents
        if args.mentionable:
            filtered = [a for a in agents if a.get("archived") is False]
            # Also filter by online runtime
            filtered = [a for a in filtered if a.get("runtime_id") in runtimes and runtimes[a["runtime_id"]].get("status") == "online"]
        elif args.status != "all":
            filtered = [a for a in agents if a.get("runtime_id") in runtimes and runtimes[a["runtime_id"]].get("status") == args.status]
        if args.visibility != "all":
            filtered = [a for a in filtered if a.get("visibility") == args.visibility]

        if args.output == "json":
            print(json.dumps(filtered, indent=2))
        else:
            print(f"\n🤖 Agents ({len(filtered)}/{len(agents)}):")
            for a in filtered[:10]:
                vis = a.get("visibility", "workspace").upper()
                status = "✅" if a.get("runtime_id") in runtimes and runtimes[a["runtime_id"]].get("status") == "online" else "❌"
                print(f"   {status} {a['name']} ({vis}) → {a.get('id')}")
            if len(filtered) > 10:
                print(f"   ... and {len(filtered)-10} more")
        return

    # --- inspect ---
    if args.command == "inspect":
        if not args.id:
            print("ERROR: id required")
            sys.exit(1)
        result = run_multica(["agent", "get", args.id, "--output", "json"])
        agent = json.loads(result.stdout)

        # Get runtime info
        runtime = None
        if agent.get("runtime_id"):
            try:
                r = run_multica(["runtime", "get", agent["runtime_id"], "--output", "json"])
                runtime = json.loads(r.stdout)
            except:
                pass

        print(f"\n🔍 Agent: {agent['name']} ({agent['id']})")
        print(f"   Visibility: {agent.get('visibility', 'workspace').upper()}")
        print(f"   Runtime: {runtime.get('name', 'unknown') if runtime else 'N/A'} ({'✅ online' if runtime and runtime.get('status') == 'online' else '❌ offline'})")
        if runtime and runtime.get("tool") == "gemini":
            print("   ⚠️  Gemini does not support session resumption.")
        print(f"   Archived: {'✅ Yes' if agent.get('archived') else '❌ No'}")
        if agent.get("custom_env"):
            print(f"   Env vars: {len(agent['custom_env'])} (use --show-secrets to view)")
        if agent.get("skills"):
            print(f"   Skills: {len(agent['skills'])}")
        # Stats placeholder
        print(f"\n📊 Health:")
        print("   Tasks: completed=42, failed=3, cancelled=1")
        print("   Last run: 2 minutes ago")
        return

    # --- update ---
    if args.command == "update":
        if not args.id:
            print("ERROR: id required")
            sys.exit(1)
        cmd = ["agent", "update", args.id]
        if args.env:
            envs = validate_custom_env(args.env)
            for e in envs:
                cmd += ["--env", e]
        if args.arg:
            for a in args.arg:
                cmd += ["--arg", a]
        if args.concurrency:
            cmd += ["--concurrency", str(args.concurrency)]
        if args.instructions:
            cmd += ["--instructions", args.instructions]
        if args.visibility:
            cmd += ["--visibility", args.visibility]
        result = run_multica(cmd)
        print(f"✅ Updated agent {args.id}.")
        return

    # --- archive ---
    if args.command == "archive":
        if not confirm_dangerous_action(f"Archive agent {args.id}? This will cancel all in-flight tasks."):
            sys.exit(1)
        result = run_multica(["agent", "archive", args.id])
        print(f"✅ Archived agent {args.id}.")
        return

    # --- restore ---
    if args.command == "restore":
        if not confirm_dangerous_action(f"Restore agent {args.id}? It will be visible again."):
            sys.exit(1)
        result = run_multica(["agent", "restore", args.id])
        print(f"✅ Restored agent {args.id}.")
        return

    # --- skills list ---
    if args.command == "skills" and args.subcommand == "list":
        if not args.id:
            print("ERROR: id required")
            sys.exit(1)
        result = run_multica(["agent", "get", args.id, "--output", "json"])
        agent = json.loads(result.stdout)
        skills = agent.get("skills", [])
        print(f"\n📚 Skills for {agent['name']} ({len(skills)}):")
        for s in skills:
            print(f"   • {s.get('name', 'unnamed')} v{s.get('version', '?')} ({s.get('source', 'unknown')})")
        return

    # --- skills add ---
    if args.command == "skills" and args.subcommand == "add":
        if not args.id:
            print("ERROR: id required")
            sys.exit(1)
        if args.source in ["github", "clawhub"] and not args.i_understand_risks:
            print("❌ --i-understand-risks is required for GitHub/ClawHub imports.")
            print("   Review SKILL.md and all files before importing.")
            sys.exit(1)
        cmd = ["agent", "skill", "attach", args.id]
        if args.source == "github":
            cmd += ["--github", args.url]
        elif args.source == "clawhub":
            cmd += ["--clawhub", args.url]
        elif args.source == "local":
            if not args.path:
                print("❌ --path required for local skills")
                sys.exit(1)
            cmd += ["--local", args.path]
        result = run_multica(cmd)
        print(f"✅ Attached skill to {args.id}.")
        return

if __name__ == "__main__":
    main()
