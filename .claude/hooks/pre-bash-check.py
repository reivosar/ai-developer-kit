#!/usr/bin/env python3
"""
Allow-list check for pre-bash.sh.
Reads JSON from stdin, checks the command against settings.json permissions.allow.

Two-stage check:
  1. Command must match an entry in permissions.allow (whitelist)
  2. Command must not match a secondary blocklist (dangerous sub-commands
     within otherwise-allowed prefixes, and shell overwrites of existing files)

Exit 0 = allowed, Exit 2 = blocked.
"""
import sys
import json
import fnmatch
import os
import re

settings_path = sys.argv[1]

try:
    data = json.load(sys.stdin)
    command = data.get("tool_input", {}).get("command", "")
except Exception:
    sys.exit(0)  # unparseable — defer to Claude Code's own permission layer

if not command:
    sys.exit(0)

try:
    with open(settings_path) as f:
        settings = json.load(f)
    allow_entries = settings.get("permissions", {}).get("allow", [])
except Exception as e:
    print(f"BLOCKED: could not read settings.json — {e}", file=sys.stderr)
    sys.exit(2)

# ── Stage 1: whitelist ────────────────────────────────────────────────────────
patterns = [
    entry[5:-1]
    for entry in allow_entries
    if entry.startswith("Bash(") and entry.endswith(")")
]

matched = any(fnmatch.fnmatch(command, p) for p in patterns)

if not matched:
    print(f"BLOCKED: command not in allow list: {command[:300]}", file=sys.stderr)
    sys.exit(2)

# ── Stage 2: secondary blocklist ─────────────────────────────────────────────
# Catches dangerous variants of allowed prefixes.

def block(reason):
    print(f"BLOCKED: {reason}", file=sys.stderr)
    sys.exit(2)

# git stash drop / clear — permanently destroys stashed work
if re.search(r"git\s+stash\s+(drop|clear)", command):
    block("'git stash drop/clear' permanently deletes stashed work. "
          "Run 'git stash list' to review stashes before dropping.")

# git checkout -- <file|.> — discards uncommitted local changes, unrecoverable
if re.search(r"git\s+checkout\s+--", command):
    block("'git checkout --' discards uncommitted changes permanently. "
          "Use 'git diff' to review changes first, or 'git stash' to save them.")

# git branch -D — force-deletes a branch, possibly losing unmerged commits
if re.search(r"git\s+branch\s+-D\b", command):
    block("'git branch -D' force-deletes a branch. "
          "Use 'git branch -d' (safe delete) — it refuses to delete unmerged branches.")

# shell redirect > to an existing file — overwrites without warning
# Detects patterns like: cmd > file, cmd 2> file, cmd 1> file
# Does NOT block >> (append) or >& (fd redirect)
overwrite_match = re.search(r"(?<![>2])\s>(?![>&])\s*(\S+)", command)
if overwrite_match:
    target = overwrite_match.group(1)
    # Expand ~ if present
    target = os.path.expanduser(target)
    if os.path.exists(target):
        block(f"shell redirect '>' would overwrite existing file '{target}'. "
              f"Use '>>' to append, or remove the file first if overwriting is intended.")

sys.exit(0)
