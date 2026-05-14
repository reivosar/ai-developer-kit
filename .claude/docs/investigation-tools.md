## Investigation Tools

Tool definitions for codebase investigation. To switch an implementation, change the `active:` value to another entry in that section's tool list.

Template variables filled at use time: `{{symbol}}` (function, class, or variable name), `{{dir}}` (search root, default `.`), `{{ext}}` (file extension without dot, e.g. `ts`, `py`), `{{pattern}}` (filename glob).

---

### symbol_search
Locate where a symbol is defined or used.

active: grep

- **grep** (with extension filter): `grep -rn "{{symbol}}" {{dir}} --include="*.{{ext}}"`
- **grep** (all file types): `grep -rn "{{symbol}}" {{dir}}`
- **rg** (with extension filter): `rg -n "{{symbol}}" {{dir}} -t {{ext}}`
- **rg** (all file types): `rg -n "{{symbol}}" {{dir}}`

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
- **rg** (all file types): `rg -n "{{symbol}}"`

---

### history_search
Find commits that introduced or modified a symbol or string.

active: git_log

- **git_log**: `git log --oneline -S "{{symbol}}"`

---

### static_analysis
Run language-native checks to surface type errors, undefined references, and lint violations without reading source files. Select the tool that matches the project's language. Run before reading any source file when diagnosing errors or verifying a change.

- **tsc**: `tsc --noEmit` (TypeScript)
- **go_vet**: `go vet ./...` (Go)
- **pylint**: `pylint {{target}}` (Python — errors and code issues)
- **flake8**: `flake8 {{target}}` (Python — PEP 8 and errors)
- **javac**: `javac -cp {{classpath}} {{target}}` (Java)
