#!/bin/bash
set -e

# Activate virtual environment
source venv/bin/activate

# Function to cleanup
cleanup() {
    echo "Stopping API server..."
    if [ -n "$SERVER_PID" ]; then
        kill $SERVER_PID || true
    fi
}

# Register cleanup function
trap cleanup EXIT

# Start API server in background
echo "Starting API server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
SERVER_PID=$!

# Wait for server to be ready
echo "Waiting for server to start..."
sleep 5

# Run tests
echo "Running tests..."
python tests/test_all_apis.py
