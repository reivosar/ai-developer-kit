#!/usr/bin/env bash
# Java and Kotlin linters for static-analysis.sh, which sources this file and
# provides require_tool, check_file_length, exit_code, LINT_CONFIG, and
# LINT_JAR_DIR.

#######################################
# Lint Java files with Checkstyle and the kit's Javadoc and file length rules,
# reported in English whatever the machine's language.
# Globals:
#   LINT_JAR_DIR, LINT_CONFIG: read. exit_code: set to 1 on a finding.
# Arguments:
#   The Java files.
# Outputs:
#   Checkstyle's findings, to stdout.
#######################################
lint_java() {
    require_tool checkstyle || return
    java -Duser.language=en -jar "$LINT_JAR_DIR/checkstyle.jar" \
        -c "$LINT_CONFIG/checkstyle-docs.xml" "$@" || exit_code=1
}

#######################################
# Lint Kotlin files with detekt and the kit's KDoc rules; detekt has no file
# length rule, so their lines are counted.
# Globals:
#   LINT_JAR_DIR, LINT_CONFIG: read. exit_code: set to 1 on a finding.
# Arguments:
#   The Kotlin files.
# Outputs:
#   detekt's findings, to stdout.
#######################################
lint_kotlin() {
    check_file_length "$@"
    require_tool detekt || return
    java -jar "$LINT_JAR_DIR/detekt.jar" --config "$LINT_CONFIG/detekt-docs.yml" \
        --input "$(IFS=,; echo "$*")" || exit_code=1
}
