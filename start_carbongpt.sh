#!/bin/bash
cd /home/runner/workspace
export PYTHONPATH=/home/runner/workspace

# Kill any process holding port 5000 or 3000 by PID
for PORT in 5000 3000; do
  PIDS=$(lsof -ti:$PORT 2>/dev/null)
  if [ -n "$PIDS" ]; then
    echo "Killing processes on port $PORT: $PIDS"
    kill -9 $PIDS 2>/dev/null || true
  fi
done

# Also kill by name
pkill -9 -f "streamlit" 2>/dev/null || true
pkill -9 -f "uvicorn" 2>/dev/null || true
pkill -9 -f "ai_review_worker.py" 2>/dev/null || true
pkill -9 -f "tsx server/index" 2>/dev/null || true
pkill -9 -f "node_modules/.bin/tsx" 2>/dev/null || true

# Wait until both ports are confirmed free
for PORT in 5000 3000; do
  for i in {1..15}; do
    if ! lsof -ti:$PORT > /dev/null 2>&1; then
      echo "Port $PORT is free"
      break
    fi
    echo "Waiting for port $PORT to free (attempt $i)..."
    sleep 1
  done
done

PORT=5000 NODE_ENV=development node_modules/.bin/tsx server/index.ts >> /tmp/node_app.log 2>&1 &

setsid nohup /home/runner/workspace/.pythonlibs/bin/python -u carbongpt/core/ai_review_worker.py \
  >> /tmp/ai_worker.log 2>&1 &

exec /home/runner/workspace/.pythonlibs/bin/python -u -m uvicorn carbongpt.app.main:app \
  --host 0.0.0.0 --port 3000 --timeout-keep-alive 300 --log-level info
