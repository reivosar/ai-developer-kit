---
name: investigate
description: Locate the code or files relevant to the current task. Use this skill at the start of any implementation, test, or simplification task to find entry points, symbols, and conventions before writing anything.
---

# Investigate

Locate the code relevant to the current task. Read and search only — no file changes.

## Setup

Always read:
- `.claude/docs/investigation-tools.md`

## Arguments

`$ARGUMENTS` describes what to locate: a symbol, file, error string, or feature area.

## Steps

### 1. Choose the right tool

Select based on what you know:

| Situation | Tool |
|---|---|
| Know a function or class name | `symbol_search` |
| Know a filename or directory pattern | `file_locate` |
| Need to find callers or references | `reference_search` |
| Debugging — have an error string | `symbol_search` on the error string |

Use one tool at a time. Read only the files it surfaces — do not read speculatively.

### 2. Report findings

Return:
- Files identified as relevant, with paths
- Key symbols or entry points found
- Conventions observed (framework, naming, error handling, patterns)
