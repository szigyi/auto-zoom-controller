#!/usr/bin/env bash

set -euo pipefail

usage() {
    cat <<'EOF'
Usage: bump_version.sh {major|minor|patch} [--dry-run] [--push]

Create the next annotated vMAJOR.MINOR.PATCH Git tag.
  --dry-run  Show the next tag without creating it.
  --push     Push the new tag to origin after creating it.
EOF
}

if [[ ${1:-} == "-h" || ${1:-} == "--help" ]]; then
    usage
    exit 0
fi

if [[ $# -lt 1 ]]; then
    usage >&2
    exit 2
fi

bump_type=$1
shift
dry_run=false
push_tag=false

for option in "$@"; do
    case "$option" in
        --dry-run)
            dry_run=true
            ;;
        --push)
            push_tag=true
            ;;
        *)
            printf 'Unknown option: %s\n' "$option" >&2
            usage >&2
            exit 2
            ;;
    esac
done

if [[ "$dry_run" == true && "$push_tag" == true ]]; then
    printf '%s\n' "--dry-run cannot be combined with --push." >&2
    exit 2
fi

case "$bump_type" in
    major|minor|patch) ;;
    *)
        printf 'Invalid version part: %s\n' "$bump_type" >&2
        usage >&2
        exit 2
        ;;
esac

if ! repo_root=$(git rev-parse --show-toplevel 2>/dev/null); then
    printf '%s\n' "Run this script from inside a Git repository." >&2
    exit 1
fi
cd "$repo_root"

latest_tag=""
while IFS= read -r candidate; do
    if [[ "$candidate" =~ ^v([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
        latest_tag=$candidate
        major=${BASH_REMATCH[1]}
        minor=${BASH_REMATCH[2]}
        patch=${BASH_REMATCH[3]}
        break
    fi
done < <(git tag --list 'v*' --sort=-version:refname)

if [[ -z "$latest_tag" ]]; then
    printf '%s\n' "No stable vMAJOR.MINOR.PATCH tag found; create the initial version tag first." >&2
    exit 1
fi

case "$bump_type" in
    major)
        major=$((major + 1))
        minor=0
        patch=0
        ;;
    minor)
        minor=$((minor + 1))
        patch=0
        ;;
    patch)
        patch=$((patch + 1))
        ;;
esac

next_tag="v${major}.${minor}.${patch}"

if git rev-parse -q --verify "refs/tags/$next_tag" >/dev/null; then
    printf 'Tag already exists: %s\n' "$next_tag" >&2
    exit 1
fi

if [[ "$dry_run" == true ]]; then
    printf 'Next tag after %s: %s (dry run; no tag created)\n' "$latest_tag" "$next_tag"
    exit 0
fi

if [[ -n $(git status --porcelain) ]]; then
    printf '%s\n' "Working tree is not clean; commit or stash changes before tagging." >&2
    exit 1
fi

git tag -a "$next_tag" -m "Release $next_tag"
printf 'Created annotated tag %s\n' "$next_tag"

if [[ "$push_tag" == true ]]; then
    git push origin "$next_tag"
else
    printf 'Push it to start the release workflow: git push origin %s\n' "$next_tag"
fi
