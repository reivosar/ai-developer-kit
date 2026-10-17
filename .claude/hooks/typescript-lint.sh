#!/usr/bin/env bash
# TypeScript linters for static-analysis.sh, which sources this file and
# provides require_tool, exit_code, LINT_CONFIG, and MAX_FILE_LINES.

# The installer reads the same prefix, so a test can point both elsewhere.
export LINT_NODE_PREFIX="${LINT_NODE_PREFIX:-$LINT_CONFIG}"

#######################################
# Tell whether the current directory holds an ESLint configuration.
# Returns:
#   0 when it does, 1 otherwise.
#######################################
has_eslint_config() {
    local name
    for name in eslint.config.js eslint.config.mjs eslint.config.cjs \
        eslint.config.ts .eslintrc .eslintrc.js .eslintrc.cjs .eslintrc.json \
        .eslintrc.yml .eslintrc.yaml; do
        [ -f "$name" ] && return 0
    done
    return 1
}

#######################################
# Tell whether the current directory holds a Biome configuration.
# Returns:
#   0 when it does, 1 otherwise.
#######################################
has_biome_config() {
    [ -f biome.json ] || [ -f biome.jsonc ]
}

#######################################
# Lint TypeScript files with the project's own linter rules plus max-lines.
# A project that configured ESLint is linted by its rules; any other project
# gets Biome, with its own configuration or else the kit's.
# Globals:
#   exit_code: set to 1 on a finding.
# Arguments:
#   The files to lint.
# Outputs:
#   The findings, to stdout.
#######################################
lint_typescript() {
    if has_eslint_config; then
        if require_tool npx; then
            npx --no-install eslint --rule "max-lines: [error, $MAX_FILE_LINES]" "$@" \
                || exit_code=1
        fi
    elif require_tool biome; then
        if has_biome_config; then
            biome lint "$@" || exit_code=1
        else
            biome lint --config-path "$LINT_CONFIG" "$@" || exit_code=1
        fi
    fi
}

#######################################
# Lint the JSDoc comments of TypeScript files with eslint-plugin-jsdoc, under
# the kit's own config, whatever linter the project uses.
# Globals:
#   exit_code: set to 1 on a finding.
#   LINT_NODE_PREFIX: where ESLint and the plugin are installed.
# Arguments:
#   The files to lint.
# Outputs:
#   The findings, to stdout.
#######################################
lint_typescript_docs() {
    require_tool eslint-jsdoc || return
    "$LINT_NODE_PREFIX/node_modules/.bin/eslint" --config "$LINT_CONFIG/eslint-jsdoc.config.mjs" \
        --no-warn-ignored "$@" || exit_code=1
}
