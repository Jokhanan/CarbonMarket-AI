#!/bin/bash
# start_local.sh — Lance CarbonGPT en local (backend FastAPI + frontend Express/Vite).
# Usage : ./start_local.sh   (depuis WSL, à la racine du dépôt)
# Arrêt : Ctrl+C (arrête les deux processus proprement)

set -e
cd "$(dirname "${BASH_SOURCE[0]}")"

if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

export DATABASE_URL="${DATABASE_URL:-postgresql://postgres:carbongpt@localhost:5432/carbongpt}"
export PYTHONPATH="${PYTHONPATH:-.}"
export PORT="${PORT:-5000}"

if ! pg_isready -q; then
    echo "Démarrage de PostgreSQL..."
    sudo systemctl start postgresql
fi

echo "Démarrage du backend FastAPI (port 3000)..."
./.venv/bin/python -m uvicorn carbongpt.app.main:app --host 0.0.0.0 --port 3000 --log-level info &
BACKEND_PID=$!

cleanup() {
    echo ""
    echo "Arrêt des serveurs..."
    kill "$BACKEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

sleep 2
echo "Démarrage du frontend (port $PORT)..."
echo ""
echo "  Application : http://localhost:$PORT"
echo "  API directe : http://localhost:3000/docs"
echo ""
NODE_ENV=development npx tsx server/index.ts
