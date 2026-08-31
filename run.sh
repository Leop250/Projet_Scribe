#!/bin/bash
cd "$(dirname "$0")"

BACKEND_PORT=8000
FRONTEND_PORT=5173
BACKEND_DIR="$PWD/backend"

free_ports() {
  for port in "$BACKEND_PORT" "$FRONTEND_PORT"; do
    pids=$(lsof -ti "tcp:$port" 2>/dev/null)
    [ -n "$pids" ] && kill -9 $pids 2>/dev/null
  done
}

cleanup() {
  trap - EXIT INT TERM
  kill -9 $(jobs -p) 2>/dev/null
  free_ports
}

free_ports
trap cleanup EXIT INT TERM

(cd backend && exec ./venv/bin/uvicorn main:app --reload \
  --port "$BACKEND_PORT" \
  --reload-exclude "$BACKEND_DIR/venv") &
(cd frontend && exec npm run dev) &

wait
