#!/bin/sh
set -eu
python -m pip install --user -r requirements.txt
python -m compileall app client automation
