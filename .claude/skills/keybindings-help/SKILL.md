---
name: keybindings-help
description: Show available Claude Code keyboard shortcuts or customize keybindings.
  Use when the user asks "what are the shortcuts", "how do I bind X", or wants
  to change a keyboard shortcut.
---

# Keybindings Help

Show Claude Code keyboard shortcuts or customize them.

## Arguments

`$ARGUMENTS` is optional. If empty, show all shortcuts. If a specific action is
given (e.g. "how do I cancel"), show the relevant shortcut.

## Built-in shortcuts (Claude Code defaults)

| Action | Shortcut |
|---|---|
| Submit message | Enter |
| Newline in input | Shift+Enter or Option+Enter |
| Interrupt / cancel running task | Escape |
| Navigate history (previous) | Up arrow |
| Navigate history (next) | Down arrow |
| Clear conversation | /clear |
| Open settings | /config |

## Customization

Claude Code does not currently support rebinding the built-in shortcuts above.

For **IDE extensions** (VS Code, JetBrains): keyboard shortcuts are managed
through the IDE's native keybinding system. Search for "Claude" in the IDE's
keyboard shortcut settings.

## If the user wants to rebind

1. Confirm what they want to change and in which environment (terminal / VS Code / JetBrains)
2. For IDE: guide them to the IDE keybinding UI and the relevant command name
3. For terminal: explain that terminal shortcuts are not configurable in Claude Code settings
4. If the request cannot be fulfilled, file a feedback issue via `/feedback`
