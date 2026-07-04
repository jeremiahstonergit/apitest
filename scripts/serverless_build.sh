#!/bin/sh
set -eu
python scripts/merge_task_catalogs.py
python -m pip install --user -r requirements.txt
python -m compileall app client automation
