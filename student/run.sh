#!/usr/bin/env bash
# Start both FastAPI and Streamlit servers for the student education system.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Student Education System ==="
echo "Starting FastAPI on port 8000 and Streamlit on port 8501..."
echo ""

# Start FastAPI in background
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload &
FASTAPI_PID=$!
echo "FastAPI started (PID: $FASTAPI_PID)"

# Wait a moment for FastAPI to start
sleep 2

# Start Streamlit in foreground
streamlit run ui/app.py --server.port 8501 --server.address 0.0.0.0 &
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
