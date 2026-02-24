#!/bin/bash
cd /home/runner/workspace
export PYTHONPATH=/home/runner/workspace
exec /home/runner/workspace/.pythonlibs/bin/uvicorn carbongpt.app.main:app --host 0.0.0.0 --port 3000
