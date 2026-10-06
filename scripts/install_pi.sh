#!/usr/bin/env bash

set -euo pipefail

REPOSITORY_URL="${AUTO_ZOOM_REPOSITORY_URL:-https://github.com/szigyi/auto-zoom-controller.git}"
INSTALL_DIR="${AUTO_ZOOM_INSTALL_DIR:-$HOME/dev/auto-zoom-controller}"

log() {
    printf '[install] %s\n' "$*"
}

fail() {
    printf '[install] Error: %s\n' "$*" >&2
    exit 1
}

if [[ ${1:-} == "-h" || ${1:-} == "--help" ]]; then
    printf '%s\n' \
        "Usage: install_pi.sh" \
        "Installs Auto Zoom Controller on Raspberry Pi OS (Bookworm or Bullseye)." \
        "Set AUTO_ZOOM_INSTALL_DIR to choose the clone/install directory." \
        "Set AUTO_ZOOM_REPOSITORY_URL to install from a different Git repository."
    exit 0
fi

if [[ $# -gt 0 ]]; then
    fail "Unknown argument: $1 (use --help for usage)."
fi

[[ "$(uname -s)" == "Linux" ]] || fail "This installer supports Raspberry Pi OS on Linux only."

case "$(uname -m)" in
    aarch64|armv6l|armv7l|armv8l) ;;
    *) fail "Unsupported architecture: $(uname -m). Run this on a Raspberry Pi." ;;
esac

[[ -r /proc/device-tree/model ]] || fail "Cannot identify Raspberry Pi hardware from /proc/device-tree/model."
pi_model=$(tr -d '\0' < /proc/device-tree/model)
[[ "$pi_model" == *"Raspberry Pi"* ]] || fail "Unsupported hardware: $pi_model."

[[ -r /etc/os-release ]] || fail "Cannot identify the operating system (/etc/os-release is missing)."
# shellcheck disable=SC1091
source /etc/os-release

case "${ID:-}" in
    debian|raspbian) ;;
    *) fail "Unsupported operating system: ${PRETTY_NAME:-unknown}. Raspberry Pi OS is required." ;;
esac

case "${VERSION_CODENAME:-}" in
    bookworm)
        gpio_package="rpi-lgpio>=0.6"
        ;;
    bullseye)
        gpio_package="RPi.GPIO"
        ;;
    *)
        fail "Unsupported Raspberry Pi OS release: ${VERSION_CODENAME:-unknown}. Supported releases are Bookworm and Bullseye."
        ;;
esac

if ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 9))'; then
    fail "Python 3.9 or newer is required; found $(python3 --version 2>&1)."
fi

if (( EUID == 0 )); then
    SUDO=()
else
    command -v sudo >/dev/null 2>&1 || fail "sudo is required to install system packages."
    SUDO=(sudo)
fi

log "Installing system packages."
"${SUDO[@]}" apt-get update
"${SUDO[@]}" apt-get install -y python3-venv python3-pip git

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" 2>/dev/null && pwd || true)
if [[ -n "$script_dir" && -f "$script_dir/../pyproject.toml" ]]; then
    PROJECT_DIR=$(cd -- "$script_dir/.." && pwd)
elif [[ -f "$PWD/pyproject.toml" && -d "$PWD/src/auto_zoom_controller" ]]; then
    PROJECT_DIR=$(pwd)
else
    if [[ -e "$INSTALL_DIR" ]]; then
        [[ -f "$INSTALL_DIR/pyproject.toml" ]] \
            || fail "Install directory already exists and is not an Auto Zoom Controller checkout: $INSTALL_DIR"
        PROJECT_DIR=$(cd -- "$INSTALL_DIR" && pwd)
        log "Using existing checkout at $PROJECT_DIR."
    else
        mkdir -p "$(dirname -- "$INSTALL_DIR")"
        log "Cloning Auto Zoom Controller into $INSTALL_DIR."
        git clone --depth 1 "$REPOSITORY_URL" "$INSTALL_DIR"
        PROJECT_DIR=$(cd -- "$INSTALL_DIR" && pwd)
    fi
fi

VENV_DIR="$PROJECT_DIR/.venv"
if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    log "Creating virtual environment at $VENV_DIR."
    python3 -m venv "$VENV_DIR"
fi

if ! "$VENV_DIR/bin/python" -c 'import sys; sys.exit(sys.version_info < (3, 9))'; then
    fail "The existing virtual environment must use Python 3.9 or newer: $VENV_DIR"
fi

log "Installing GPIO driver for ${VERSION_CODENAME}."
"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/python" -m pip install "$gpio_package"

log "Installing Auto Zoom Controller."
"$VENV_DIR/bin/python" -m pip install -e "$PROJECT_DIR"

log "Verifying command-line installation."
"$VENV_DIR/bin/auto-zoom" --help >/dev/null
"$VENV_DIR/bin/auto-zoom" --dry-run -i 0.5 -d 0.05 -s 20

mkdir -p "$HOME/bin"
runner_path="$HOME/bin/auto-zoom"
printf -v executable_path '%q' "$VENV_DIR/bin/auto-zoom"
printf '#!/usr/bin/env bash\nexec %s "$@"\n' "$executable_path" > "$runner_path"
chmod +x "$runner_path"
"$runner_path" --help >/dev/null

log "Installation complete. Run $runner_path to start the controller."
case ":${PATH}:" in
    *":$HOME/bin:"*) ;;
    *) log "Add $HOME/bin to PATH to run auto-zoom without its full path." ;;
esac
