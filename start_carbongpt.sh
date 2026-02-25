#!/bin/bash
cd /home/runner/workspace
export PYTHONPATH=/home/runner/workspace

/home/runner/workspace/.pythonlibs/bin/uvicorn carbongpt.app.main:app --host 0.0.0.0 --port 3000 &

exec /home/runner/workspace/.pythonlibs/bin/streamlit run carbongpt/ui/streamlit_app.py --server.port 5000 --server.headless true --server.address 0.0.0.0 --server.enableCORS false --server.enableXsrfProtection false
