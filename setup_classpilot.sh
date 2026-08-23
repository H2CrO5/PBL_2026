#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "Python interpreter not found: $PYTHON_BIN" >&2
    exit 1
fi

if ! "$PYTHON_BIN" -c 'import sys; raise SystemExit(sys.version_info < (3, 10))'; then
    echo "ClassPilot requires Python 3.10 or newer (found: $("$PYTHON_BIN" --version 2>&1))." >&2
    echo "Set PYTHON_BIN to a newer interpreter, for example: PYTHON_BIN=python3.12 ./setup_classpilot.sh" >&2
    exit 1
fi

"$PYTHON_BIN" -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r student/requirements.txt -r teacher/requirements.txt

(cd student && ../.venv/bin/python -m db.seed)
(cd teacher && ../.venv/bin/python -m db.seed)

if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env. Add your Bedrock key and integration token before starting."
fi

echo "Setup complete. Run: ./run_classpilot.sh"
