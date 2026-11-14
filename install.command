#!/bin/bash
# Double-click in Finder, or run: bash install.command
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd -P)"
DRY_RUN=0
SKIP_APP=0
OPEN_APP=1
ARGS=()
usage() {
  cat <<'END'
Usage: bash install.command [--dry-run] [--skip-app] [--no-open]
                            [--profile NAME] [--replace-conflicts]

--dry-run            Validate/preview rules; do not install software or change files.
--skip-app           Only manage rules; do not install Karabiner-Elements.
--no-open            Do not launch Karabiner-Elements Settings when done.
--profile NAME       Named Karabiner profile (default: selected).
--replace-conflicts  Explicitly replace rules using the same Safari shortcut.
END
}
while (( $# )); do
  case "$1" in
    --dry-run) DRY_RUN=1; ARGS+=(--dry-run); shift ;;
    --skip-app) SKIP_APP=1; shift ;;
    --no-open) OPEN_APP=0; shift ;;
    --replace-conflicts) ARGS+=(--replace-conflicts); shift ;;
    --profile)
      if (( $# < 2 )); then echo 'Missing value after --profile' >&2; exit 2; fi
      ARGS+=(--profile "$2"); shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done
if [[ "$(uname -s)" != "Darwin" ]]; then
  echo 'macOS only. Run the Python unit tests on Linux.' >&2; exit 1
fi
if [[ "$(id -u)" -eq 0 ]]; then
  echo 'Do not use sudo: Karabiner rules belong to your normal user.' >&2; exit 1
fi
have_brew() {
  command -v brew >/dev/null 2>&1 || [[ -x /opt/homebrew/bin/brew ]] || [[ -x /usr/local/bin/brew ]]
}
setup_brew_path() {
  local candidate
  for candidate in /opt/homebrew/bin/brew /usr/local/bin/brew; do
    if [[ -x "$candidate" ]]; then eval "$("$candidate" shellenv)"; return 0; fi
  done
}
install_brew() {
  if have_brew; then setup_brew_path; return 0; fi
  if ! command -v curl >/dev/null 2>&1; then
    echo 'curl required for official Homebrew installer.' >&2; return 1
  fi
  echo 'Homebrew is missing. The official bootstrap script will be downloaded and run.'
  echo 'Official information: https://brew.sh/'
  printf 'Install Homebrew now? [y/N] '
  read -r answer
  case "$answer" in y|Y|yes|YES) ;; *) echo 'Cancelled.' >&2; return 1 ;; esac
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  setup_brew_path
  if ! command -v brew >/dev/null 2>&1; then
    echo 'Homebrew installation returned but brew is not available.' >&2; return 1
  fi
}
resolve_python() {
  local candidate
  for candidate in /opt/homebrew/bin/python3 /usr/local/bin/python3; do
    if [[ -x "$candidate" ]] && "$candidate" -c 'import json' >/dev/null 2>&1; then
      PYTHON="$candidate"; return 0
    fi
  done
  if command -v python3 >/dev/null 2>&1 && python3 -c 'import json' >/dev/null 2>&1; then
    PYTHON="$(command -v python3)"; return 0
  fi
  return 1
}
PYTHON=''
if (( DRY_RUN )); then
  if ! resolve_python; then
    echo 'Python 3 is needed for --dry-run. No software was installed.' >&2; exit 1
  fi
  "$PYTHON" "$PROJECT_DIR/scripts/manage_rules.py" validate
  "$PYTHON" "$PROJECT_DIR/scripts/manage_rules.py" install "${ARGS[@]}"
  echo 'Dry run complete; nothing changed.'
  exit 0
fi
if (( ! SKIP_APP )); then
  if [[ -d /Applications/Karabiner-Elements.app ]] || /usr/bin/open -Ra 'Karabiner-Elements' >/dev/null 2>&1; then
    echo 'Karabiner-Elements already installed; app installation skipped.'
  else
    install_brew
    brew install --cask karabiner-elements
  fi
fi
if ! resolve_python; then
  echo 'Python 3 is needed to modify JSON safely.'
  install_brew
  brew install python
  if ! resolve_python; then echo 'Python 3 unavailable after installation.' >&2; exit 1; fi
fi
"$PYTHON" "$PROJECT_DIR/scripts/manage_rules.py" validate
"$PYTHON" "$PROJECT_DIR/scripts/manage_rules.py" install "${ARGS[@]}"
if (( OPEN_APP )); then
  if /usr/bin/open -Ra 'Karabiner-Elements' >/dev/null 2>&1; then
    /usr/bin/open -a 'Karabiner-Elements' || echo 'Open Karabiner-Elements manually.'
  else
    echo 'Open Karabiner-Elements Settings manually to finish setup.'
  fi
fi
cat <<'END'

Completed. The rule is active in the selected Karabiner profile and stored
as a predefined rule. macOS still requires approval of background services,
Accessibility and Driver Extension. Test Command+Backtick with two Safari windows.
END
