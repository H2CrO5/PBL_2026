#!/usr/bin/env bash
# Start both FastAPI and Streamlit servers for the teacher module.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Load shared local configuration when present. The real .env is gitignored.
if [ -f "$SCRIPT_DIR/../.env" ]; then
    set -a
    source "$SCRIPT_DIR/../.env"
    set +a
fi

echo "=== Teacher Education System ==="
echo "Starting FastAPI on port 8100 and Streamlit on port 8601..."
echo ""

uvicorn api.main:app --host 0.0.0.0 --port 8100 --reload &
FASTAPI_PID=$!
echo "FastAPI started (PID: $FASTAPI_PID)"

sleep 2

streamlit run ui/app.py --server.port 8601 --server.address 0.0.0.0 &
STREAMLIT_PID=$!
echo "Streamlit started (PID: $STREAMLIT_PID)"

echo ""
echo "FastAPI:   http://localhost:8100"
echo "Streamlit: http://localhost:8601"
echo "API docs:  http://localhost:8100/docs"
echo ""
echo "Press Ctrl+C to stop both servers."

trap "echo 'Shutting down...'; kill $FASTAPI_PID $STREAMLIT_PID 2>/dev/null; exit 0" INT TERM

wait
