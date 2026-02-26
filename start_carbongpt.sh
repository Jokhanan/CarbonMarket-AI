#!/bin/bash
cd /home/runner/workspace
export PYTHONPATH=/home/runner/workspace

pkill -f "ai_review_worker.py" 2>/dev/null || true
sleep 0.5

/home/runner/workspace/.pythonlibs/bin/streamlit run carbongpt/ui/streamlit_app.py --server.port 5000 --server.headless true --server.address 0.0.0.0 --server.enableCORS false --server.enableXsrfProtection false &

setsid nohup /home/runner/workspace/.pythonlibs/bin/python -u carbongpt/core/ai_review_worker.py >> /tmp/ai_worker.log 2>&1 &

exec /home/runner/workspace/.pythonlibs/bin/python -u -m uvicorn carbongpt.app.main:app --host 0.0.0.0 --port 3000 --timeout-keep-alive 300 --log-level info
