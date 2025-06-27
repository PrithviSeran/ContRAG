#!/bin/bash
# Startup script for GraphRAG backend server
# Properly handles PORT environment variable for deployment platforms

set -e

# Get port from environment variable, default to 8000
PORT=${PORT:-8000}

# Validate port is numeric
if ! [[ "$PORT" =~ ^[0-9]+$ ]] || [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
    echo "Error: Invalid port value '$PORT'. Must be a number between 1-65535."
    exit 1
fi

# Get host, default to 0.0.0.0 for deployment
HOST=${HOST:-0.0.0.0}

# Check if USE_GUNICORN is set to true
if [ "${USE_GUNICORN,,}" = "true" ]; then
    echo "Starting server with gunicorn on $HOST:$PORT"
    exec gunicorn api:app \
        --bind "$HOST:$PORT" \
        --worker-class uvicorn.workers.UvicornWorker \
        --workers 1 \
        --timeout 300 \
        --access-logfile - \
        --error-logfile -
else
    echo "Starting server with uvicorn on $HOST:$PORT"
    exec uvicorn api:app \
        --host "$HOST" \
        --port "$PORT" \
        --access-log \
        --timeout-keep-alive 300
fi 