#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

PORT=8501
if [ $# -gt 0 ] && [[ "$1" =~ ^[0-9]+$ ]]; then
    PORT="$1"
    shift
fi

cd "$PROJECT_ROOT"
echo "Iniciando dashboard em http://127.0.0.1:$PORT..."
exec .venv/bin/streamlit run app/app.py --server.address 127.0.0.1 --server.port "$PORT" "$@"
