#!/usr/bin/env python3
"""Minimal MCP-like stdio server for SpaceWeb operation lookup.

Tools:
- search_operation(query, limit=10)
- get_schema(operationId)
- get_example(operationId)

This is intentionally minimal and dependency-light.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / 'spec' / 'openapi.llm-projection.yaml'
EXAMPLES = ROOT / 'examples' / 'examples.jsonl'


def load_state():
    spec = yaml.safe_load(SPEC.read_text(encoding='utf-8'))
    ops = []
    by_id = {}
    for path, item in (spec.get('paths') or {}).items():
        post = (item or {}).get('post')
        if not post:
            continue
        op = {
            'operationId': post.get('operationId'),
            'summary': post.get('summary', ''),
            'path': path,
            'upstreamPath': post.get('x-sweb-upstream-path'),
            'upstreamMethod': post.get('x-sweb-upstream-method'),
            'requestSchema': (((post.get('requestBody') or {}).get('content') or {}).get('application/json') or {}).get('schema'),
            'responseSchema': ((((post.get('responses') or {}).get('200') or {}).get('content') or {}).get('application/json') or {}).get('schema'),
        }
        if op['operationId']:
            ops.append(op)
            by_id[op['operationId']] = op

    examples = {}
    if EXAMPLES.exists():
        for line in EXAMPLES.read_text(encoding='utf-8').splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            op_id = row.get('operationId')
            if op_id:
                examples[op_id] = row

    return ops, by_id, examples


OPS, OPS_BY_ID, EXAMPLES_BY_ID = load_state()


def tool_search_operation(args: Dict[str, Any]) -> Dict[str, Any]:
    q = (args.get('query') or '').lower().strip()
    limit = int(args.get('limit') or 10)
    scored = []
    for op in OPS:
        hay = ' '.join([
            op.get('operationId') or '',
            op.get('summary') or '',
            op.get('path') or '',
            op.get('upstreamPath') or '',
            op.get('upstreamMethod') or '',
        ]).lower()
        if not q:
            score = 1
        elif q in hay:
            score = 100 - hay.index(q)
        else:
            continue
        scored.append((score, op))
    scored.sort(key=lambda x: x[0], reverse=True)
    return {'items': [x[1] for x in scored[:limit]], 'count': len(scored)}


def tool_get_schema(args: Dict[str, Any]) -> Dict[str, Any]:
    op_id = args.get('operationId')
    if not op_id or op_id not in OPS_BY_ID:
        return {'error': f'Unknown operationId: {op_id}'}
    op = OPS_BY_ID[op_id]
    return {
        'operationId': op_id,
        'upstreamPath': op.get('upstreamPath'),
        'upstreamMethod': op.get('upstreamMethod'),
        'requestSchema': op.get('requestSchema'),
        'responseSchema': op.get('responseSchema'),
    }


def tool_get_example(args: Dict[str, Any]) -> Dict[str, Any]:
    op_id = args.get('operationId')
    if not op_id:
        return {'error': 'operationId is required'}
    ex = EXAMPLES_BY_ID.get(op_id)
    if not ex:
        return {'error': f'No example for operationId: {op_id}'}
    return ex


def _namespace_for(op: Dict[str, Any]) -> str:
    up = (op.get('upstreamPath') or '').strip('/')
    if not up:
        return 'root'
    parts = up.split('/')
    return '.'.join(parts)


def tool_list_operations_by_namespace(args: Dict[str, Any]) -> Dict[str, Any]:
    namespace = (args.get('namespace') or '').strip()
    limit = int(args.get('limit') or 100)
    items = []
    for op in OPS:
        ns = _namespace_for(op)
        if namespace and not ns.startswith(namespace):
            continue
        items.append({
            'operationId': op.get('operationId'),
            'summary': op.get('summary'),
            'namespace': ns,
            'upstreamPath': op.get('upstreamPath'),
            'upstreamMethod': op.get('upstreamMethod'),
        })
    items = sorted(items, key=lambda x: (x['namespace'], x['operationId']))[:limit]
    return {'items': items, 'count': len(items)}


def tool_resolve_transport_call(args: Dict[str, Any]) -> Dict[str, Any]:
    op_id = args.get('operationId')
    params = args.get('params') or {}
    req_id = args.get('id')
    user = args.get('user')
    token = args.get('token')

    op = OPS_BY_ID.get(op_id)
    if not op:
        return {'error': f'Unknown operationId: {op_id}'}

    path = op.get('upstreamPath')
    method = op.get('upstreamMethod')
    with_auth = not (path == '/notAuthorized/' and method == 'getToken')

    body = {'jsonrpc': '2.0', 'method': method, 'params': params}
    if req_id is not None:
        body['id'] = req_id
    if user is not None:
        body['user'] = user

    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json',
    }
    if with_auth and token:
        headers['Authorization'] = f'Bearer {token}'

    return {
        'operationId': op_id,
        'urlPath': path,
        'httpMethod': 'POST',
        'withAuth': with_auth,
        'headers': headers,
        'jsonBody': body,
    }


TOOLS = {
    'search_operation': {
        'description': 'Search operation by name/summary/path',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'query': {'type': 'string'},
                'limit': {'type': 'integer', 'default': 10},
            },
            'required': ['query'],
            'additionalProperties': False,
        },
        'fn': tool_search_operation,
    },
    'get_schema': {
        'description': 'Get request/response schema for operationId',
        'inputSchema': {
            'type': 'object',
            'properties': {'operationId': {'type': 'string'}},
            'required': ['operationId'],
            'additionalProperties': False,
        },
        'fn': tool_get_schema,
    },
    'get_example': {
        'description': 'Get example payloads for operationId',
        'inputSchema': {
            'type': 'object',
            'properties': {'operationId': {'type': 'string'}},
            'required': ['operationId'],
            'additionalProperties': False,
        },
        'fn': tool_get_example,
    },
    'list_operations_by_namespace': {
        'description': 'List operations grouped/filterable by namespace (e.g. domains.bonus)',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'namespace': {'type': 'string'},
                'limit': {'type': 'integer', 'default': 100},
            },
            'additionalProperties': False,
        },
        'fn': tool_list_operations_by_namespace,
    },
    'resolve_transport_call': {
        'description': 'Resolve operationId + params into real JSON-RPC transport call payload',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'operationId': {'type': 'string'},
                'params': {'type': 'object'},
                'id': {'type': 'string'},
                'user': {'type': 'string'},
                'token': {'type': 'string'},
            },
            'required': ['operationId', 'params'],
            'additionalProperties': False,
        },
        'fn': tool_resolve_transport_call,
    },
}


def send(msg: Dict[str, Any]):
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + '\n')
    sys.stdout.flush()


def handle(req: Dict[str, Any]):
    method = req.get('method')
    req_id = req.get('id')
    params = req.get('params') or {}

    if method == 'initialize':
        return {
            'jsonrpc': '2.0',
            'id': req_id,
            'result': {
                'protocolVersion': '2024-11-05',
                'capabilities': {'tools': {}},
                'serverInfo': {'name': 'sweb-api-mcp', 'version': '0.1.0'},
            },
        }

    if method == 'tools/list':
        tools = []
        for name, meta in TOOLS.items():
            tools.append({'name': name, 'description': meta['description'], 'inputSchema': meta['inputSchema']})
        return {'jsonrpc': '2.0', 'id': req_id, 'result': {'tools': tools}}

    if method == 'tools/call':
        name = params.get('name')
        args = params.get('arguments') or {}
        tool = TOOLS.get(name)
        if not tool:
            return {'jsonrpc': '2.0', 'id': req_id, 'error': {'code': -32601, 'message': f'Unknown tool {name}'}}
        data = tool['fn'](args)
        return {
            'jsonrpc': '2.0',
            'id': req_id,
            'result': {
                'content': [
                    {'type': 'text', 'text': json.dumps(data, ensure_ascii=False, indent=2)}
                ]
            },
        }

    # notifications
    if method in ('initialized',):
        return None

    return {'jsonrpc': '2.0', 'id': req_id, 'error': {'code': -32601, 'message': f'Unknown method {method}'}}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            continue
        resp = handle(req)
        if resp is not None:
            send(resp)


if __name__ == '__main__':
    main()
