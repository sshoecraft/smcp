#!/usr/bin/env python3
"""Drive a running ask-smcp-server over stdio and call its `query` tool.

Exercises the same path Claude Code uses (`ask-smcp-server --insecure`, credentials
from the environment) without needing the MCP client to restart. Credentials are
read from a named `claude mcp` registration so no key is typed on the command line.

Usage:
    python3 tests/stdio_query.py ask_astra "What is 2+2? Answer with the digit only."
    python3 tests/stdio_query.py ask_astra "..." --effort low --max-tokens 2000
"""

import argparse
import json
import os
import subprocess
import sys

CRED_KEYS = (
    "ASK_TYPE",
    "ASK_API_KEY",
    "ASK_MODEL",
    "ASK_BASE_URL",
    "ASK_MAX_TOKENS",
    "ASK_SYSTEM",
    "ASK_TIMEOUT",
    "ASK_THINKING_LEVEL",
    "ASK_REASONING_EFFORT",
    "ASK_AUTO_CONTINUE",
)


def registration_env(name):
    """Pull the env block out of `claude mcp get <name>`."""
    out = subprocess.run(
        ["claude", "mcp", "get", name],
        capture_output=True, text=True, check=True,
    ).stdout
    env = {}
    for line in out.splitlines():
        line = line.strip()
        key, sep, value = line.partition("=")
        if sep and key in CRED_KEYS:
            env[key] = value
    if not env:
        raise SystemExit(f"no ASK_* credentials found in registration '{name}'")
    return env


class StdioClient:
    """Minimal MCP JSON-RPC client over a child process's stdin/stdout."""

    def __init__(self, command, env):
        child_env = dict(os.environ)
        child_env.update(env)
        self.proc = subprocess.Popen(
            command,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, bufsize=1, env=child_env,
        )
        self.next_id = 0

    def send(self, method, params, want_reply=True):
        message = {"jsonrpc": "2.0", "method": method, "params": params}
        if want_reply:
            self.next_id += 1
            message["id"] = self.next_id
        self.proc.stdin.write(json.dumps(message) + "\n")
        self.proc.stdin.flush()
        if not want_reply:
            return None
        while True:
            line = self.proc.stdout.readline()
            if not line:
                raise SystemExit(
                    "server closed stdout before replying:\n"
                    + self.proc.stderr.read()
                )
            reply = json.loads(line)
            if reply.get("id") == message["id"]:
                return reply

    def close(self):
        self.proc.stdin.close()
        self.proc.terminate()
        self.proc.wait(timeout=10)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registration", help="name of the `claude mcp` registration to borrow creds from")
    parser.add_argument("prompt", help="prompt to send to the query tool")
    parser.add_argument("--effort", help="override ASK_REASONING_EFFORT for this run")
    parser.add_argument("--max-tokens", type=int, help="per-call max_tokens override")
    parser.add_argument("--command", default="ask-smcp-server", help="server binary (default: ask-smcp-server)")
    args = parser.parse_args()

    env = registration_env(args.registration)
    if args.effort:
        env["ASK_REASONING_EFFORT"] = args.effort

    client = StdioClient([args.command, "--insecure"], env)
    try:
        client.send("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "stdio_query", "version": "1.0"},
        })
        client.send("notifications/initialized", {}, want_reply=False)

        listed = client.send("tools/list", {})
        tools = listed.get("result", {}).get("tools", [])
        print("tools:", ", ".join(tool["name"] for tool in tools))
        for tool in tools:
            if tool["name"] == "query":
                print("description:", tool.get("description", "").strip().splitlines()[0])

        call_args = {"prompt": args.prompt}
        if args.max_tokens:
            call_args["max_tokens"] = args.max_tokens
        reply = client.send("tools/call", {"name": "query", "arguments": call_args})
    finally:
        client.close()

    if "error" in reply:
        print("ERROR:", json.dumps(reply["error"], indent=2))
        return 1

    result = reply.get("result", {})
    for block in result.get("content", []):
        if block.get("type") == "text":
            print(block["text"])
    structured = result.get("structuredContent")
    if structured:
        print(json.dumps(structured, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
