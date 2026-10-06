#!/usr/bin/env bash

set -euo pipefail

usage() {
    printf '%s\n' \
        "Usage: install_web_service.sh [--dry-run|--uninstall]" \
        "Install the per-user systemd service for the localhost dry-run web UI." \
        "Run as the Raspberry Pi user; no sudo is required."
}

dry_run=false
uninstall=false
case "${1:-}" in
    "") ;;
    --dry-run) dry_run=true ;;
    --uninstall) uninstall=true ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
esac

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
project_dir=$(cd -- "$script_dir/.." && pwd)
unit_template="$project_dir/scripts/systemd/autozoom-web.service"
web_command="$project_dir/.venv/bin/auto-zoom-web"

[[ -f "$unit_template" ]] || { printf 'Missing service template: %s\n' "$unit_template" >&2; exit 1; }
[[ -x "$web_command" ]] || { printf 'Missing %s; install the [web] extra first.\n' "$web_command" >&2; exit 1; }
[[ "$project_dir" != *[[:space:]]* ]] || {
    printf '%s\n' "Project path contains whitespace, which this unit template does not support." >&2
    exit 1
}

escaped_project_dir=${project_dir//&/\\&}
escaped_project_dir=${escaped_project_dir//|/\\|}
render_unit() {
    sed "s|@PROJECT_DIR@|$escaped_project_dir|g" "$unit_template"
}

if [[ "$dry_run" == true ]]; then
    render_unit
    exit 0
fi

[[ "$(uname -s)" == "Linux" ]] || {
    printf '%s\n' "The user service requires Linux with systemd." >&2
    exit 1
}
command -v systemctl >/dev/null 2>&1 || {
    printf '%s\n' "systemctl was not found; install this service on a systemd-based Raspberry Pi OS." >&2
    exit 1
}
systemctl --user show-environment >/dev/null 2>&1 || {
    printf '%s\n' "No systemd user manager is available. Log in to the Pi as this user and retry." >&2
    exit 1
}

unit_dir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
if [[ "$uninstall" == true ]]; then
    systemctl --user disable --now autozoom-web.service >/dev/null 2>&1 || true
    rm -f "$unit_dir/autozoom-web.service"
    systemctl --user daemon-reload
    printf '%s\n' "Removed autozoom-web.service."
    exit 0
fi

mkdir -p "$unit_dir"
temporary_unit=$(mktemp)
trap 'rm -f "$temporary_unit"' EXIT
render_unit > "$temporary_unit"
install -m 0644 "$temporary_unit" "$unit_dir/autozoom-web.service"
systemctl --user daemon-reload
systemctl --user enable --now autozoom-web.service

printf '%s\n' "Installed and started autozoom-web.service."
printf '%s\n' "The UI is loopback-only; use SSH forwarding to access it remotely."
printf 'For startup before login, enable lingering with: sudo loginctl enable-linger %s\n' "$USER"
