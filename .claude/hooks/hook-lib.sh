#!/usr/bin/env bash
# Shared hook utilities for bash hooks.
# Usage: source "$(dirname "${BASH_SOURCE[0]}")/hook-lib.sh"
HOOKS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$HOOKS_DIR" rev-parse --show-toplevel)"
