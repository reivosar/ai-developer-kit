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

# nearest_project <directory> <marker> prints the nearest directory at or
# above directory that holds marker, or nothing.
nearest_project() {
    local directory="$1" marker="$2"
    while :; do
        [ -f "$directory/$marker" ] && { echo "$directory"; return; }
        [ -z "$directory" ] && return
        directory="${directory%/*}"
    done
}

# projects_of <marker> <file>... prints "project <dir>" once for each project
# the files belong to, and "file <path>" for a file that belongs to none.
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

# type_check_project <dir> runs tsc on a TypeScript project. tsc has no cache of
# its own, so --incremental keeps what one run learned for the next; the record
# goes under ~/.cache, never into the project. go vet and clippy cache their
# results themselves.
type_check_project() {
    if [ -z "${HOME:-}" ]; then
        tsc --noEmit -p "$1"
        return
    fi
    local build_info="$HOME/.cache/ai-developer-kit/tsc/${1//\//_}.tsbuildinfo"
    tsc --noEmit -p "$1" --incremental --tsBuildInfoFile "$build_info"
}

# check_projects <marker> <file>... runs the module check once in each project
# the files belong to and sets exit_code on a finding. clippy cannot check a
# file outside a Cargo package; saying so keeps that from reading as clean.
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
