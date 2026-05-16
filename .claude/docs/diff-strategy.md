## Diff Reading Strategy

### Purpose of the threshold

The threshold triggers a context-splitting mode — it does NOT indicate review
importance. Generated files, lockfiles, snapshots, vendor code, or migration
SQL can exceed the threshold instantly. A 40-line dense security change still
requires full scrutiny. The threshold only determines HOW to read the diff,
never WHETHER to review it.

### Size check

Always run `--stat` first:

```bash
git diff --stat <range>        # branch or PR review
git diff --staged --stat       # commit
```

Read the summary line: `N files changed, X insertions(+), Y deletions(-)`.

```
DIFF_LINE_THRESHOLD = 500   (X + Y from the summary line)
```

### Under threshold — read all at once

```bash
git diff <range>
git diff --staged
```

### Over threshold — enumerate files, then read per-file

Do NOT skip any file. Get the file list safely (handles spaces in paths):

```bash
git diff --name-only <range>       # branch
git diff --staged --name-only      # commit
gh pr diff $PR --name-only         # PR
```

Then for each file:

```bash
git diff <range> -- <file>
git diff --staged -- <file>
gh pr diff $PR -- <file>
```

Review every file without exception. For an extremely large single file, read
the diff in chunks using line-range filters if needed — do not skip it.
