#!/bin/bash
set -e

cd "$(dirname "$0")"

trap 'kill 0' EXIT INT TERM

(cd backend && ./venv/bin/uvicorn main:app --reload) &
(cd frontend && npm run dev) &

wait
