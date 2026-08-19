#!/usr/bin/env bash
# Start both FastAPI and Streamlit servers for the student education system.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

TOOL_DIR="$SCRIPT_DIR/../.venv/bin"
if [ ! -x "$TOOL_DIR/uvicorn" ] || [ ! -x "$TOOL_DIR/streamlit" ]; then
    echo "Missing .venv. Run ./setup_classpilot.sh from the repository root first."
    exit 1
fi

# Load shared local configuration when present. The real .env is gitignored.
if [ -f "$SCRIPT_DIR/../.env" ]; then
    set -a
    source "$SCRIPT_DIR/../.env"
    set +a
fi

echo "=== ClassPilot Student ==="
echo "Starting FastAPI on port 8000 and Streamlit on port 8501..."
echo ""

# Start FastAPI in background
"$TOOL_DIR/uvicorn" api.main:app --host 0.0.0.0 --port 8000 --reload &
FASTAPI_PID=$!
echo "FastAPI started (PID: $FASTAPI_PID)"

# Wait a moment for FastAPI to start
sleep 2

# Start Streamlit in foreground
"$TOOL_DIR/streamlit" run ui/app.py --server.port 8501 --server.address 0.0.0.0 &
STREAMLIT_PID=$!
echo "Streamlit started (PID: $STREAMLIT_PID)"

echo ""
echo "FastAPI:   http://localhost:8000"
echo "Streamlit: http://localhost:8501"
echo "API docs:  http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers."

# Trap Ctrl+C to kill both processes
trap "echo 'Shutting down...'; kill $FASTAPI_PID $STREAMLIT_PID 2>/dev/null; exit 0" INT TERM

# Wait for either process to exit
wait
