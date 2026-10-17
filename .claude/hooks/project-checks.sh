#!/usr/bin/env bash
# Whole-module checks for static-analysis.sh, which sources this file:
# go vet, tsc, and clippy check a whole module, so each runs in the project a
# file belongs to, not in the directory the script was started from.
# Builtins only: the tests run the script with a PATH of stand-ins.

# Public Rust items carry doc comments, with the Errors, Panics, and Safety
# sections the Rust API guidelines ask for.
RUST_DOC_LINTS=(
    -D missing_docs -D clippy::missing_errors_doc -D clippy::missing_panics_doc
    -D clippy::missing_safety_doc
)

#######################################
# Find the nearest directory at or above a directory that holds a marker file.
# Arguments:
#   The directory to start from, then the marker's file name.
# Outputs:
#   The directory found, to stdout; nothing when none holds the marker.
#######################################
nearest_project() {
    local directory="$1" marker="$2"
    while :; do
        [ -f "$directory/$marker" ] && { echo "$directory"; return; }
        [ -z "$directory" ] && return
        directory="${directory%/*}"
    done
}

#######################################
# Group files by the project each belongs to.
# Arguments:
#   The marker file that makes a directory a project, then the files.
# Outputs:
#   "project <dir>" once for each project, and "file <path>" for each file
#   that belongs to none, to stdout.
#######################################
projects_of() {
    local marker="$1" file folder project seen=$'\n'
    shift
    for file in "$@"; do
        case "$file" in */*) folder="${file%/*}" ;; *) folder=. ;; esac
        project=$(nearest_project "$(cd "${folder:-/}" && pwd -P)" "$marker")
        if [ -z "$project" ]; then
            echo "file $file"
            continue
        fi
        case "$seen" in *$'\n'"$project"$'\n'*) continue ;; esac
        seen="$seen$project"$'\n'
        echo "project $project"
    done
}

#######################################
# Type-check a TypeScript project. tsc has no cache of its own, so
# --incremental keeps what one run learned for the next; the record goes
# under ~/.cache, never into the project. go vet and clippy cache their
# results themselves.
# Globals:
#   HOME
# Arguments:
#   The project's directory, the one holding tsconfig.json.
# Outputs:
#   tsc's findings, to stdout.
#######################################
type_check_project() {
    if [ -z "${HOME:-}" ]; then
        tsc --noEmit -p "$1"
        return
    fi
    local build_info="$HOME/.cache/ai-developer-kit/tsc/${1//\//_}.tsbuildinfo"
    tsc --noEmit -p "$1" --incremental --tsBuildInfoFile "$build_info"
}

#######################################
# Run the module check (go vet, tsc, clippy) once in each project the files
# belong to. clippy cannot check a file outside a Cargo package; saying so
# keeps that from reading as clean.
# Globals:
#   RUST_DOC_LINTS: read. exit_code: set to 1 on a finding.
# Arguments:
#   The marker file (go.mod, tsconfig.json, or Cargo.toml), then the files.
# Outputs:
#   The checks' findings, to stdout; a Rust file in no package, to stderr.
#######################################
check_projects() {
    local marker="$1" kind path
    shift
    while read -r kind path; do
        case "$marker $kind" in
            "go.mod project") go -C "$path" vet ./... ;;
            "go.mod file") go vet "$path" ;;
            "tsconfig.json project") type_check_project "$path" ;;
            "tsconfig.json file") tsc --noEmit "$path" ;;
            "Cargo.toml project")
                cargo clippy --manifest-path "$path/Cargo.toml" --all-targets --quiet -- \
                    -D warnings "${RUST_DOC_LINTS[@]}" ;;
            "Cargo.toml file")
                echo "static-analysis: $path belongs to no Cargo package, so clippy did not check it." >&2 ;;
        esac </dev/null || exit_code=1
    done < <(projects_of "$marker" "$@")
}
