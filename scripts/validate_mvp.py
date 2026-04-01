import json
from pathlib import Path
from typing import Any, Dict

import yaml

ROOT = Path(__file__).resolve().parent.parent
SPEC_PROJECTION = ROOT / 'spec' / 'openapi.llm-projection.yaml'
SPEC_TRANSPORT = ROOT / 'spec' / 'openapi.transport.yaml'
EXAMPLES = ROOT / 'examples' / 'examples.jsonl'
PY_OPS = ROOT / 'client' / 'python' / 'operations.generated.json'
TS_OPS = ROOT / 'client' / 'ts' / 'operations.generated.json'


def collect_ops(spec):
    ops = []
    for path, item in (spec.get('paths') or {}).items():
        post = (item or {}).get('post')
        if post:
            ops.append((path, post))
    return ops


def get_params_schema(op):
    try:
        return op['requestBody']['content']['application/json']['schema']['properties']['params']
    except Exception:
        return {'type': 'object', 'properties': {}, 'additionalProperties': True}


def get_result_schema(op):
    try:
        return op['responses']['200']['content']['application/json']['schema']['properties']['result']
    except Exception:
        return {}


def is_nullable(schema: Dict[str, Any]) -> bool:
    if not isinstance(schema, dict):
        return False
    if schema.get('nullable') is True:
        return True
    t = schema.get('type')
    return isinstance(t, list) and 'null' in t


def type_name(v: Any) -> str:
    if v is None:
        return 'null'
    if isinstance(v, bool):
        return 'boolean'
    if isinstance(v, int) and not isinstance(v, bool):
        return 'integer'
    if isinstance(v, float):
        return 'number'
    if isinstance(v, str):
        return 'string'
    if isinstance(v, list):
        return 'array'
    if isinstance(v, dict):
        return 'object'
    return type(v).__name__


def validate_value(
    schema: Dict[str, Any],
    value: Any,
    path: str,
    errors: list[str],
    *,
    enforce_required: bool = True,
    enforce_additional: bool = True,
    allow_null_any: bool = False,
):
    if value is None:
        if allow_null_any or is_nullable(schema):
            return
        errors.append(f'{path}: null is not allowed')
        return

    expected = schema.get('type')
    if isinstance(expected, list):
        expected_no_null = [t for t in expected if t != 'null']
        for t in expected_no_null:
            local = []
            validate_value({'type': t, **{k: v for k, v in schema.items() if k != 'type'}}, value, path, local, enforce_required=enforce_required, enforce_additional=enforce_additional, allow_null_any=allow_null_any)
            if not local:
                return
        errors.append(f'{path}: value type {type_name(value)} does not match any of {expected}')
        return

    if expected == 'integer':
        if not (isinstance(value, int) and not isinstance(value, bool)):
            if isinstance(value, str):
                import re
                if re.search(r'-?\d+', value.replace(',', '.')):
                    return
            errors.append(f'{path}: expected integer, got {type_name(value)}')
            return
    elif expected == 'number':
        if not (isinstance(value, (int, float)) and not isinstance(value, bool)):
            if isinstance(value, str):
                import re
                if re.search(r'-?\d+(?:\.\d+)?', value.replace(',', '.')):
                    return
            errors.append(f'{path}: expected number, got {type_name(value)}')
            return
    elif expected == 'boolean':
        if not isinstance(value, bool):
            errors.append(f'{path}: expected boolean, got {type_name(value)}')
            return
    elif expected == 'string':
        if not isinstance(value, str):
            errors.append(f'{path}: expected string, got {type_name(value)}')
            return
    elif expected == 'array':
        if not isinstance(value, list):
            errors.append(f'{path}: expected array, got {type_name(value)}')
            return
        item_schema = schema.get('items') or {}
        for i, item in enumerate(value):
            validate_value(item_schema, item, f'{path}[{i}]', errors, enforce_required=enforce_required, enforce_additional=enforce_additional, allow_null_any=allow_null_any)
        return
    elif expected == 'object':
        if not isinstance(value, dict):
            errors.append(f'{path}: expected object, got {type_name(value)}')
            return
        props = schema.get('properties') or {}
        required = schema.get('required') or []
        if enforce_required:
            for req in required:
                if req not in value:
                    errors.append(f'{path}.{req}: required property is missing')
        for k, v in value.items():
            if k in props:
                validate_value(props[k], v, f'{path}.{k}', errors, enforce_required=enforce_required, enforce_additional=enforce_additional, allow_null_any=allow_null_any)
            else:
                ap = schema.get('additionalProperties', True)
                if ap is False and enforce_additional:
                    errors.append(f'{path}.{k}: additional property is not allowed')
                elif isinstance(ap, dict):
                    validate_value(ap, v, f'{path}.{k}', errors, enforce_required=enforce_required, enforce_additional=enforce_additional, allow_null_any=allow_null_any)
        return

    enum = schema.get('enum')
    if enum is not None and value not in enum:
        errors.append(f'{path}: value {value!r} not in enum {enum}')


def main():
    projection = yaml.safe_load(SPEC_PROJECTION.read_text(encoding='utf-8'))
    transport = yaml.safe_load(SPEC_TRANSPORT.read_text(encoding='utf-8')) if SPEC_TRANSPORT.exists() else {'paths': {}}

    proj_ops = collect_ops(projection)
    tr_paths = set((transport.get('paths') or {}).keys())

    errors: list[str] = []

    # 1) operationId unique
    ids = [op.get('operationId') for _, op in proj_ops if op.get('operationId')]
    dup = sorted({x for x in ids if ids.count(x) > 1})
    if dup:
        errors.append(f'Duplicate operationId: {dup}')

    # 2) upstream path sanity + projection/transport consistency
    for path, op in proj_ops:
        up = op.get('x-sweb-upstream-path')
        if up is None:
            continue
        if not up.startswith('/') or not up.endswith('/'):
            errors.append(f'Bad x-sweb-upstream-path at {path}: {up}')
            continue
        if up not in tr_paths:
            errors.append(f'Upstream path missing in transport spec for {op.get("operationId")}: {up}')

    # 3) generated operation maps consistency
    expected_map = {}
    for _, op in proj_ops:
        op_id = op.get('operationId')
        if not op_id:
            continue
        expected_map[op_id] = {
            'operationId': op_id,
            'upstreamPath': op.get('x-sweb-upstream-path'),
            'upstreamMethod': op.get('x-sweb-upstream-method'),
        }

    for label, path in [('python', PY_OPS), ('ts', TS_OPS)]:
        if path.exists():
            actual = json.loads(path.read_text(encoding='utf-8'))
            if actual != expected_map:
                errors.append(f'Operation map mismatch for {label}: expected {len(expected_map)} ops, got {len(actual)}')

    # 4) example validation for request+response
    by_id = {op.get('operationId'): op for _, op in proj_ops if op.get('operationId')}
    if EXAMPLES.exists():
        for idx, line in enumerate(EXAMPLES.read_text(encoding='utf-8').splitlines(), 1):
            if not line.strip():
                continue
            row = json.loads(line)
            op_id = row.get('operationId')
            op = by_id.get(op_id)
            if not op:
                errors.append(f'Line {idx}: unknown operationId {op_id}')
                continue

            params_schema = get_params_schema(op)
            req_params = row.get('request', {}).get('params', {})
            if not isinstance(req_params, dict):
                errors.append(f'Line {idx}: params must be object')
            else:
                validate_value(params_schema, req_params, f'Line {idx}:{op_id}.params', errors)

            result_schema = get_result_schema(op)
            resp_result = row.get('response_success', {}).get('result')
            validate_value(
                result_schema,
                resp_result,
                f'Line {idx}:{op_id}.result',
                errors,
                enforce_required=False,
                enforce_additional=False,
                allow_null_any=True,
            )

    if errors:
        print('VALIDATION FAILED')
        for e in errors:
            print('-', e)
        raise SystemExit(1)

    print('VALIDATION OK')
    print(f'Checked operations: {len(proj_ops)}')


if __name__ == '__main__':
    main()
