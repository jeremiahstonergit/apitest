#!/bin/sh
set -eu
python -m scripts.merge_task_catalogs
python -m pip install --user -r requirements.txt
python -m compileall app client automation
