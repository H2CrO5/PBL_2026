#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== ClassPilot ==="
echo "Student UI: http://localhost:8501"
echo "Teacher UI: http://localhost:8601"
echo "Press Ctrl+C to stop all services."

bash "$PROJECT_DIR/student/run.sh" &
STUDENT_PID=$!
bash "$PROJECT_DIR/teacher/run.sh" &
TEACHER_PID=$!

shutdown() {
    echo "Stopping ClassPilot..."
    kill "$STUDENT_PID" "$TEACHER_PID" 2>/dev/null || true
    wait "$STUDENT_PID" "$TEACHER_PID" 2>/dev/null || true
}

trap shutdown INT TERM EXIT
wait
