#!/bin/sh
# Single-container startup: the Help chatbot runs as its own process (its own
# Cognee singleton — see help_api/config.py for why), the main API fronts it
# by reverse-proxying /help/* to 127.0.0.1:8010 (see api/main.py).
set -e

uvicorn help_api.main:app --host 127.0.0.1 --port 8010 &

exec uvicorn api.main:app --host 0.0.0.0 --port "${PORT:-8000}"
