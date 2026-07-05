#!/usr/bin/env python3
"""Example task used to verify the web UI and scheduler wiring."""

from __future__ import annotations

import argparse
import json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--params-json', default='{}')
    args = parser.parse_args()
    params = json.loads(args.params_json or '{}')
    print(json.dumps({'status': 'ok', 'received': params}, ensure_ascii=False))


if __name__ == '__main__':
    main()
