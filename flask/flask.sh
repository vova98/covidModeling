#!/bin/bash
PYTHONPATH=. python3 -c "from api import init_base; init_base()"
PYTHONPATH=. gunicorn --bind 0.0.0.0:$1 --timeout=86400 server:app --worker-connections 1000 -w 2 --threads 4