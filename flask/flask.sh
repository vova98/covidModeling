PYTHONPATH=flask gunicorn --bind 0.0.0.0:$1 --timeout=86400 server:app --worker-connections 1000 -w 2 --threads 4
