## Investigation Tools

Tool definitions for codebase investigation. To switch an implementation, change the `active:` value to another entry in that section's tool list.

Template variables filled at use time: `{{symbol}}` (function, class, or variable name), `{{dir}}` (search root, default `.`), `{{ext}}` (file extension without dot, e.g. `ts`, `py`; omit the flag if searching all types), `{{pattern}}` (filename glob).

---

### symbol_search
Locate where a symbol is defined or used.

active: grep

- **grep**: `grep -rn "{{symbol}}" {{dir}} --include="*.{{ext}}"`
- **rg**: `rg -n "{{symbol}}" {{dir}} -t {{ext}}`

---

### file_locate
Find files by name or path pattern.

active: find

- **find**: `find {{dir}} -name "{{pattern}}" -not -path "*/node_modules/*" -not -path "*/.git/*"`
- **fd**: `fd "{{pattern}}" {{dir}}`

---

### reference_search
Find all usages of a symbol across the tracked codebase.

active: git_grep

- **git_grep**: `git grep -n "{{symbol}}"`
- **rg**: `rg -n "{{symbol}}"`

---

### history_search
Find commits that introduced or modified a symbol or string.

active: git_log

- **git_log**: `git log --oneline -S "{{symbol}}"`
