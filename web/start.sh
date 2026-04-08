#!/usr/bin/env sh
# Reads PORT at runtime so bind address is always numeric (avoids literal "$PORT").
set -e
PORT="${PORT:-8000}"
exec gunicorn -b "0.0.0.0:${PORT}" app:app
