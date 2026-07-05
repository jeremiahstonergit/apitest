#!/usr/bin/env python3
"""Execute a SpaceWeb JSON-RPC operation from the generated operation map."""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OPERATIONS_PATH = ROOT / 'client' / 'python' / 'operations.generated.json'
DEFAULT_SERVER = 'https://api.sweb.ru'


def post_json(path: str, body: dict[str, Any], token: str | None = None) -> dict[str, Any]:
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json',
    }
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(
        f"{os.getenv('SWEB_API_SERVER', DEFAULT_SERVER).rstrip('/')}{path}",
        data=json.dumps(body, ensure_ascii=False).encode('utf-8'),
        headers=headers,
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=int(os.getenv('SWEB_API_TIMEOUT', '30'))) as response:
            payload = json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f'SpaceWeb HTTP {exc.code}: {exc.read().decode(errors="replace")}') from exc
    if isinstance(payload.get('error'), dict):
        err = payload['error']
        raise RuntimeError(f"SpaceWeb API error {err.get('code')}: {err.get('message')}")
    return payload


def get_token() -> str | None:
    token = os.getenv('SWEB_API_TOKEN')
    if token:
        return token
    login = os.getenv('SWEB_API_LOGIN')
    password = os.getenv('SWEB_API_PASSWORD')
    if not (login and password):
        return None
    payload = post_json('/notAuthorized/', {
        'jsonrpc': '2.0',
        'method': 'getToken',
        'params': {'login': login, 'password': password},
    })
    result = payload.get('result')
    if not isinstance(result, str) or not result:
        raise RuntimeError('SpaceWeb token was not returned in result')
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--params-json', default='{}')
    args = parser.parse_args()
    payload: dict[str, Any] = json.loads(args.params_json or '{}')
    operation_id = payload.pop('operation_id', None)
    if not isinstance(operation_id, str) or not operation_id:
        raise ValueError('params_json.operation_id is required')
    params = payload.pop('params', payload)
    if not isinstance(params, dict):
        raise ValueError('params must be an object')

    operations = json.loads(OPERATIONS_PATH.read_text(encoding='utf-8'))
    operation = operations.get(operation_id)
    if not operation:
        raise KeyError(f'Unknown operation_id: {operation_id}')

    token = None if operation['upstreamPath'] == '/notAuthorized/' else get_token()
    if operation['upstreamPath'] != '/notAuthorized/' and not token:
        raise RuntimeError('Set SWEB_API_TOKEN or both SWEB_API_LOGIN and SWEB_API_PASSWORD')

    body = {'jsonrpc': '2.0', 'method': operation['upstreamMethod'], 'params': params}
    if isinstance(payload.get('user'), str):
        body['user'] = payload['user']
    print(json.dumps(post_json(operation['upstreamPath'], body, token), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
