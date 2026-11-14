#!/bin/bash
# Remove only rules managed by this repository; leave the application installed.
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd -P)"
if [[ "$(uname -s)" != "Darwin" ]]; then echo 'macOS only.' >&2; exit 1; fi
if [[ "$(id -u)" -eq 0 ]]; then echo 'Run without sudo.' >&2; exit 1; fi
if ! command -v python3 >/dev/null 2>&1; then
  for py in /opt/homebrew/bin/python3 /usr/local/bin/python3; do
    if [[ -x "$py" ]]; then exec "$py" "$PROJECT_DIR/scripts/manage_rules.py" remove "$@"; fi
  done
  echo 'Python 3 not found.' >&2; exit 1
fi
exec python3 "$PROJECT_DIR/scripts/manage_rules.py" remove "$@"
