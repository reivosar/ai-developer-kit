# Kit Update Commands

Canonical commands for syncing a project with the upstream kit. Use these exact command forms. Do not paraphrase or reconstruct from memory. General git, PR, and worktree commands are in `commands.md`.

## clone-kit

```bash
gh repo clone reivosar/ai-developer-kit .upstream -- --depth=1 --quiet
```

Clones the upstream kit into `.upstream/` inside the project tree. Never run from inside an existing worktree.

## find-upstream

```bash
find . -path './.upstream/.claude/docs/*' -type f
find . -path './.upstream/.claude/rules/*' -type f
find . -path './.upstream/.claude/skills/*' -type f
find . -path './.upstream/.claude/hooks/*' -type f
```

Issue all four as a parallel batch. Enumerates all files in the upstream clone.

## find-local

```bash
find . -path './.claude/docs/*' -type f
find . -path './.claude/rules/*' -type f
find . -path './.claude/skills/*' -type f
find . -path './.claude/hooks/*' -type f
```

Issue all four as a parallel batch. Enumerates all local kit files.

## diff-upstream

```bash
diff -q .upstream/<path> <local_path>
```

Compares an upstream file against its local counterpart. Exit 0 = identical; exit 1 = differs.

## upstream-exists

```bash
test -f .upstream/<local_path>
```

Returns exit 0 if the upstream counterpart of a local file exists; exit 1 if absent.

## kit-diff-stat

```bash
git diff --stat .claude/docs/ .claude/rules/ .claude/skills/ .claude/hooks/
git status
```

Run as a parallel batch. Shows the summary of all kit file changes before committing.
