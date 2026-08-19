#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r student/requirements.txt -r teacher/requirements.txt

(cd student && ../.venv/bin/python -m db.seed)
(cd teacher && ../.venv/bin/python -m db.seed)

if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env. Add your Bedrock key and integration token before starting."
fi

echo "Setup complete. Run: ./run_classpilot.sh"
