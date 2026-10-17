#!/usr/bin/env bash
# Checks static-analysis.sh makes on a file's text itself, where no linter
# has the rule: the 200-line limit, and the Google Shell Style Guide header
# comment of each shell function. static-analysis.sh sources this file and
# provides exit_code and MAX_FILE_LINES. Builtins only: the tests run the
# script with a PATH of stand-ins.

FUNCTION_PARENS='^[[:space:]]*(function[[:space:]]+)?([A-Za-z_][A-Za-z0-9_-]*)[[:space:]]*\(\)'
FUNCTION_KEYWORD='^[[:space:]]*function[[:space:]]+([A-Za-z_][A-Za-z0-9_-]*)'
# What a function body does that its header must then name.
USES_ARGUMENTS='\$[1-9#@*]|\$\{[1-9@*#]\}|\$\{[1-9][^}]*\}|(^|[[:space:];])shift([[:space:];]|$)'
WRITES_OUTPUT='(^|[[:space:];&|])(echo|printf)([[:space:]]|$)'
# The body is matched as one text, so the space after return is [ \t]:
# [[:space:]] would reach across a newline into the next statement.
SETS_STATUS='(^|[[:space:];&|])(return[ 	]+([1-9]|"?\$)|exit([[:space:];]|$))'

#######################################
# Fail each file longer than MAX_FILE_LINES; a last line without a newline
# counts too.
# Globals:
#   exit_code: set to 1 on a finding.
# Arguments:
#   The files to measure.
# Outputs:
#   Each file over the limit with its line count, to stdout.
#######################################
check_file_length() {
    local file line count
    for file in "$@"; do
        count=0
        while IFS= read -r line || [ -n "$line" ]; do
            count=$((count + 1))
        done < "$file"
        if [ "$count" -gt "$MAX_FILE_LINES" ]; then
            echo "$file: $count lines, more than $MAX_FILE_LINES"
            exit_code=1
        fi
    done
}

#######################################
# Read a file into SHELL_LINES, one element per line.
# Globals:
#   SHELL_LINES: set to the file's lines.
# Arguments:
#   The file to read.
#######################################
read_shell_lines() {
    local line
    SHELL_LINES=()
    while IFS= read -r line || [ -n "$line" ]; do
        SHELL_LINES+=("$line")
    done < "$1"
}

#######################################
# Set FUNCTION_NAME to the function a line defines.
# Globals:
#   FUNCTION_NAME: set to the name, or emptied.
# Arguments:
#   One line of a shell script.
# Returns:
#   1 when the line defines no function.
#######################################
function_defined_by() {
    FUNCTION_NAME=""
    if [[ "$1" =~ $FUNCTION_PARENS ]]; then
        FUNCTION_NAME="${BASH_REMATCH[2]}"
    elif [[ "$1" =~ $FUNCTION_KEYWORD ]]; then
        FUNCTION_NAME="${BASH_REMATCH[1]}"
    fi
    [ -n "$FUNCTION_NAME" ]
}

#######################################
# Set HEADER_TEXT to the comment lines right above a function, leaving out
# shellcheck directives.
# Globals:
#   SHELL_LINES: read. HEADER_TEXT: set.
# Arguments:
#   The index of the function's line.
#######################################
read_header() {
    local index=$(($1 - 1)) line
    HEADER_TEXT=""
    while [ "$index" -ge 0 ] && [[ "${SHELL_LINES[$index]}" =~ ^[[:space:]]*# ]]; do
        line="${SHELL_LINES[$index]}"
        [[ "$line" =~ ^[[:space:]]*#[[:space:]]*shellcheck ]] || HEADER_TEXT="$line"$'\n'"$HEADER_TEXT"
        index=$((index - 1))
    done
}

#######################################
# Set BODY_TEXT to a function's code lines: up to the closing brace indented
# like the definition, or else up to the next function. A definition that
# closes on its own line is its own body.
# Globals:
#   SHELL_LINES: read. BODY_TEXT: set.
# Arguments:
#   The index of the function's line, then the index of the next function.
#######################################
read_body() {
    local definition="${SHELL_LINES[$1]}" index line indent
    BODY_TEXT="$definition"$'\n'
    [[ "$definition" =~ \}[[:space:]]*$ ]] && return
    [[ "$definition" =~ ^([[:space:]]*) ]] && indent="${BASH_REMATCH[1]}"
    for ((index = $1 + 1; index < $2; index++)); do
        line="${SHELL_LINES[$index]}"
        [[ "$line" =~ ^[[:space:]]*\}[[:space:]]*$ ]] && [ "${line%%\}*}" = "$indent" ] && break
        [[ "$line" =~ ^[[:space:]]*# ]] || BODY_TEXT="$BODY_TEXT$line"$'\n'
    done
}

#######################################
# Check one function's header against what its body does.
# Globals:
#   HEADER_TEXT, BODY_TEXT: read. exit_code: set to 1 on a finding.
# Arguments:
#   Where the function is, as "file:line: name".
# Outputs:
#   Each finding, to stdout.
#######################################
check_function_header() {
    if ! [[ "$HEADER_TEXT" =~ [A-Za-z] ]]; then
        echo "$1: no header comment (Google Shell Style Guide)"
        exit_code=1
        return
    fi
    local section pattern
    for section in Arguments Outputs Returns; do
        case "$section" in
            Arguments) pattern="$USES_ARGUMENTS" ;;
            Outputs) pattern="$WRITES_OUTPUT" ;;
            Returns) pattern="$SETS_STATUS" ;;
        esac
        if [[ "$BODY_TEXT" =~ $pattern ]] && [[ "$HEADER_TEXT" != *"$section:"* ]]; then
            echo "$1: header comment lists no $section:"
            exit_code=1
        fi
    done
}

#######################################
# Check the header comment of every function in shell scripts.
# Globals:
#   exit_code: set to 1 on a finding.
# Arguments:
#   The scripts to check.
# Outputs:
#   Each finding, to stdout.
#######################################
check_shell_docs() {
    local file index starts names count
    for file in "$@"; do
        read_shell_lines "$file"
        [ ${#SHELL_LINES[@]} -gt 0 ] || continue
        starts=() names=()
        for index in "${!SHELL_LINES[@]}"; do
            function_defined_by "${SHELL_LINES[$index]}" || continue
            starts+=("$index") names+=("$FUNCTION_NAME")
        done
        starts+=("${#SHELL_LINES[@]}")
        count=$((${#starts[@]} - 1))
        for ((index = 0; index < count; index++)); do
            read_header "${starts[$index]}"
            read_body "${starts[$index]}" "${starts[$((index + 1))]}"
            check_function_header "$file:$((starts[index] + 1)): ${names[$index]}"
        done
    done
}
