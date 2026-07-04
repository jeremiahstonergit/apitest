#!/usr/bin/env python3
"""Run an allowed SpaceWeb operation by operationId from params JSON."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'client' / 'python'))

from transport import SwebTransportClient  # noqa: E402


def make_client() -> SwebTransportClient:
    client = SwebTransportClient(token=os.getenv('SWEB_API_TOKEN') or None)
    if client.token:
        return client

    login = os.getenv('SWEB_API_LOGIN')
    password = os.getenv('SWEB_API_PASSWORD')
    if not (login and password):
        raise RuntimeError('Set SWEB_API_TOKEN or both SWEB_API_LOGIN and SWEB_API_PASSWORD')
    client.get_token(login, password)
    return client


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--params-json', default='{}')
    args = parser.parse_args()
    payload: dict[str, Any] = json.loads(args.params_json or '{}')

    operation_id = payload.get('operation_id')
    if not isinstance(operation_id, str) or not operation_id:
        raise ValueError('params_json.operation_id is required')

    params = payload.get('params') or {}
    if not isinstance(params, dict):
        raise ValueError('params_json.params must be an object')

    user = payload.get('user')
    if user is not None and not isinstance(user, str):
        raise ValueError('params_json.user must be a string when provided')

    result = make_client().call_by_operation(operation_id, params=params, user=user)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
