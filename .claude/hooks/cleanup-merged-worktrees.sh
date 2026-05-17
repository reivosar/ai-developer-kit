#!/usr/bin/env bash
# Removes worktrees under .claude/worktrees/ whose branch is fully merged into main.
# Runs non-interactively; exits 0 regardless of individual failures.

set -euo pipefail

source "$(dirname "${BASH_SOURCE[0]}")/hook-lib.sh"
WORKTREES_DIR="$REPO_ROOT/.claude/worktrees"

if [[ ! -d "$WORKTREES_DIR" ]]; then
    exit 0
fi

parse_worktrees() {
    git -C "$REPO_ROOT" worktree list --porcelain
}

cleanup_merged() {
    local current_path="" current_branch=""

    while IFS= read -r line; do
        if [[ "$line" == worktree\ * ]]; then
            current_path="${line#worktree }"
            current_branch=""
        elif [[ "$line" == branch\ * ]]; then
            current_branch="${line#branch refs/heads/}"
        elif [[ -z "$line" ]]; then
            process_worktree "$current_path" "$current_branch"
            current_path=""
            current_branch=""
        fi
    done < <(parse_worktrees; echo)
}

process_worktree() {
    local path="$1" branch="$2"

    [[ "$path" == "$WORKTREES_DIR"/* ]] || return 0
    [[ -n "$branch" && "$branch" != "main" ]] || return 0

    if git -C "$REPO_ROOT" merge-base --is-ancestor "$branch" main 2>/dev/null; then
        echo "Removing merged worktree: $path (branch: $branch)"
        git -C "$REPO_ROOT" worktree remove --force "$path" 2>/dev/null || true
        git -C "$REPO_ROOT" branch -d "$branch" 2>/dev/null || true
    fi
}

git -C "$REPO_ROOT" checkout main 2>/dev/null || true
cleanup_merged
exit 0
