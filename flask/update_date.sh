#!/bin/bash
PYTHONPATH=. python3 -c "from api import init_base, update_data; init_base(); update_data();"