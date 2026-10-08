#!/usr/bin/env python3
"""
multica-llm-runtime — Vendor-agnostic Multica runtime for any LLM.
Supports: ollama, openai, litellm, http, file, text.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Optional import — only used for HTTP backends
try:
    import requests
except ImportError:
    requests = None


def get_llm_response(llm_spec: str, prompt: str, system_prompt: str = "") -> str:
    """
    Route to appropriate LLM backend based on llm_spec.
    Returns raw string response.
    """
    if llm_spec.startswith("ollama:"):
        model = llm_spec.split(":", 1)[1]
        return _call_ollama(model, prompt, system_prompt)
    
    elif llm_spec.startswith("openai:"):
        model = llm_spec.split(":", 1)[1]
        return _call_openai(model, prompt, system_prompt)
    
    elif llm_spec.startswith("litellm:"):
        model = llm_spec.split(":", 1)[1]
        return _call_litellm(model, prompt, system_prompt)
    
    elif llm_spec.startswith("http://") or llm_spec.startswith("https://"):
        return _call_http(llm_spec, prompt, system_prompt)
    
    elif llm_spec.startswith("file:"):
        path = llm_spec.split(":", 1)[1]
        with open(path) as f:
            static_prompt = f.read().strip()
        full_prompt = f"{static_prompt}\n\nUser request:\n{prompt}"
        return _call_text(full_prompt)
    
    elif llm_spec.startswith("text:"):
        static_prompt = llm_spec.split(":", 1)[1]
        full_prompt = f"{static_prompt}\n\nUser request:\n{prompt}"
        return _call_text(full_prompt)
    
    else:
        raise ValueError(f"Unsupported LLM spec: {llm_spec}")


def _call_text(prompt: str) -> str:
    return f"[SIMULATED RESPONSE]\n{prompt}\n\n✅ This is a local, deterministic reply — no LLM was called."


def _call_ollama(model: str, prompt: str, system_prompt: str = "") -> str:
    try:
        import requests
        r = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt or "You are a helpful coding assistant."},
                    {"role": "user", "content": prompt}
                ],
                "stream": False
            },
            timeout=120
        )
        r.raise_for_status()
        return r.json()["message"]["content"].strip()
    except Exception as e:
        return f"[OLLAMA ERROR] {e}"


def _call_openai(model: str, prompt: str, system_prompt: str = "") -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    try:
        import requests
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt or "You are a helpful coding assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2
            },
            timeout=120
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[OPENAI ERROR] {e}"


def _call_litellm(model: str, prompt: str, system_prompt: str = "") -> str:
    base_url = os.getenv("LITELLM_BASE_URL", "http://localhost:4000")
    api_key = os.getenv("LITELLM_API_KEY", "sk-1234")
    try:
        import requests
        r = requests.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt or "You are a helpful coding assistant."},
                    {"role": "user", "content": prompt}
                ]
            },
            timeout=120
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[LITELLM ERROR] {e}"


def _call_http(url: str, prompt: str, system_prompt: str = "") -> str:
    try:
        import requests
        r = requests.post(
            url,
            json={
                "model": "default",
                "messages": [
                    {"role": "system", "content": system_prompt or "You are a helpful coding assistant."},
                    {"role": "user", "content": prompt}
                ]
            },
            timeout=120
        )
        r.raise_for_status()
        resp = r.json()
        # Try common OpenAI-compatible fields
        if "choices" in resp and len(resp["choices"]) > 0:
            return resp["choices"][0]["message"]["content"].strip()
        elif "message" in resp:
            return resp["message"].get("content", "").strip()
        else:
            return json.dumps(resp, indent=2)
    except Exception as e:
        return f"[HTTP ERROR] {e}"


def main():
    parser = argparse.ArgumentParser(description="Multica LLM Runtime")
    parser.add_argument("command", choices=["execute", "info", "health-check"])
    parser.add_argument("task_id", nargs="?", help="Task ID (e.g., MUL-123)")
    parser.add_argument("--llm", required=False, help="LLM backend (e.g., ollama:llama3)")
    parser.add_argument("--dry-run", action="store_true", help="Print prompt only")
    args = parser.parse_args()

    if args.command == "info":
        print(json.dumps({
            "name": "multica-llm-runtime",
            "version": "0.1.0",
            "backends": ["ollama", "openai", "litellm", "http", "file", "text"],
            "capabilities": ["code", "edit", "test", "explain", "summarize"]
        }, indent=2))
        return

    if args.command == "health-check":
        tmp = Path("/tmp/multica-tasks")
        if not tmp.exists():
            print("❌ /tmp/multica-tasks does not exist")
            sys.exit(1)
        if not os.access(tmp, os.W_OK):
            print("❌ /tmp/multica-tasks is not writable")
            sys.exit(1)
        print("✅ Health check passed")
        return

    if args.command == "execute":
        if not args.task_id:
            print("ERROR: task_id required")
            sys.exit(1)
        if not args.llm:
            print("ERROR: --llm required (e.g., --llm ollama:llama3)")
            sys.exit(1)

        working_dir = Path("/tmp/multica-tasks") / args.task_id
        input_path = working_dir / "input.json"
        output_path = working_dir / "output.json"

        if not input_path.exists():
            print(f"❌ input.json not found in {working_dir}")
            sys.exit(1)

        try:
            with open(input_path) as f:
                inp = json.load(f)

            # Build prompt
            title = inp.get("issue_title", "Untitled")
            body = inp.get("issue_body", "")
            files = "\nFiles: " + ", ".join(inp.get("files", [])) if inp.get("files") else ""
            instructions = "\nInstructions: " + inp.get("instructions", "") if inp.get("instructions") else ""

            prompt = f"Task ID: {args.task_id}\nTitle: {title}\nBody: {body}{files}{instructions}"
            system_prompt = "You are a precise, code-focused AI assistant. Respond in plain text. Do not add markdown, explanations, or disclaimers — just the answer."

            if args.dry_run:
                print("=== DRY RUN — PROMPT ===")
                print(f"System: {system_prompt}")
                print(f"User: {prompt}")
                print("========================")
                sys.exit(0)

            start = time.time()
            response = get_llm_response(args.llm, prompt, system_prompt)
            duration = int(time.time() - start)

            result = {
                "status": "completed",
                "output": response,
                "artifacts": [],
                "comments": [
                    f"✅ Handled by multica-llm-runtime ({args.llm}) in {duration}s."
                ]
            }

            with open(output_path, "w") as f:
                json.dump(result, f, indent=2)

            print(f"✅ Written {output_path}")
            sys.exit(0)

        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
