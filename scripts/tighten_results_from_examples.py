from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import yaml

ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = ROOT / 'spec' / 'openapi.llm-projection.yaml'
EXAMPLES_PATH = ROOT / 'examples' / 'examples.jsonl'


def normalize_types(schema: Dict[str, Any]) -> list[str]:
    if not isinstance(schema, dict):
        return []
    t = schema.get('type')
    if isinstance(t, list):
        return list(dict.fromkeys(t))
    if isinstance(t, str):
        return [t]
    if schema.get('nullable') is True:
        return ['null']
    return []


def set_types(schema: Dict[str, Any], types: list[str]) -> Dict[str, Any]:
    types = list(dict.fromkeys(types))
    out = dict(schema)
    if not types:
        out.pop('type', None)
        return out
    if len(types) == 1:
        out['type'] = types[0]
    else:
        out['type'] = types
    if 'null' in types and out.get('nullable') is True:
        out.pop('nullable', None)
    return out


def merge_schema(left: Dict[str, Any], right: Dict[str, Any]) -> Dict[str, Any]:
    if not left:
        return right
    if not right:
        return left

    out: Dict[str, Any] = {}
    types = normalize_types(left) + normalize_types(right)
    if not types:
        types = []
    out = set_types(out, types)

    if 'object' in types:
        props = {}
        for source in (left, right):
            for key, value in (source.get('properties') or {}).items():
                if key in props:
                    props[key] = merge_schema(props[key], value)
                else:
                    props[key] = value
        if props:
            out['properties'] = props
        out['additionalProperties'] = left.get('additionalProperties', True) or right.get('additionalProperties', True)
        required = sorted(set((left.get('required') or [])) & set((right.get('required') or [])))
        if required:
            out['required'] = required

    if 'array' in types:
        l_items = left.get('items') or {}
        r_items = right.get('items') or {}
        out['items'] = merge_schema(l_items, r_items) if (l_items or r_items) else {}

    if 'enum' in left or 'enum' in right:
        enum_values = []
        for source in (left, right):
            for value in source.get('enum') or []:
                if value not in enum_values:
                    enum_values.append(value)
        if enum_values:
            out['enum'] = enum_values

    if 'description' in left and left['description']:
        out['description'] = left['description']
    elif 'description' in right and right['description']:
        out['description'] = right['description']

    return out


def infer_schema(value: Any) -> Dict[str, Any]:
    if value is None:
        return {'type': ['null']}
    if isinstance(value, bool):
        return {'type': 'boolean'}
    if isinstance(value, int) and not isinstance(value, bool):
        return {'type': 'integer'}
    if isinstance(value, float):
        return {'type': 'number'}
    if isinstance(value, str):
        return {'type': 'string'}
    if isinstance(value, list):
        item_schema: Dict[str, Any] = {}
        for item in value:
            item_schema = merge_schema(item_schema, infer_schema(item))
        return {'type': 'array', 'items': item_schema}
    if isinstance(value, dict):
        props = {k: infer_schema(v) for k, v in value.items()}
        return {
            'type': 'object',
            'properties': props,
            'additionalProperties': True,
        }
    return {}


def is_weak_result_schema(schema: Dict[str, Any]) -> bool:
    if not isinstance(schema, dict) or not schema:
        return True
    t = schema.get('type')
    if t == 'object':
        props = schema.get('properties') or {}
        ap = schema.get('additionalProperties', True)
        if (not props) and ap is True:
            return True
    if t == 'array':
        items = schema.get('items') or {}
        if not isinstance(items, dict) or not items:
            return True
        if items.get('type') == 'object':
            props = items.get('properties') or {}
            ap = items.get('additionalProperties', True)
            if (not props) and ap is True:
                return True
    return False


def loosely_matches(schema: Dict[str, Any], value: Any) -> bool:
    if value is None:
        return True
    if not isinstance(schema, dict) or not schema:
        return True
    types = normalize_types(schema)
    if not types:
        return True
    if 'null' in types:
        types = [t for t in types if t != 'null']
    if not types:
        return True
    for t in types:
        if t == 'integer' and isinstance(value, int) and not isinstance(value, bool):
            return True
        if t == 'number' and isinstance(value, (int, float)) and not isinstance(value, bool):
            return True
        if t == 'boolean' and isinstance(value, bool):
            return True
        if t == 'string' and isinstance(value, str):
            return True
        if t == 'array' and isinstance(value, list):
            items = schema.get('items') or {}
            return all(loosely_matches(items, x) for x in value)
        if t == 'object' and isinstance(value, dict):
            props = schema.get('properties') or {}
            return all((k not in props) or loosely_matches(props[k], v) for k, v in value.items())
    return False


def load_examples_by_operation() -> Dict[str, Dict[str, Any]]:
    out = {}
    if not EXAMPLES_PATH.exists():
        return out
    for line in EXAMPLES_PATH.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        op_id = row.get('operationId')
        if op_id:
            out[op_id] = row
    return out


def main() -> None:
    spec = yaml.safe_load(SPEC_PATH.read_text(encoding='utf-8'))
    by_op = load_examples_by_operation()

    tightened = 0
    scanned = 0

    for _, item in (spec.get('paths') or {}).items():
        post = (item or {}).get('post')
        if not post:
            continue
        op_id = post.get('operationId')
        scanned += 1
        if not op_id or op_id not in by_op:
            continue

        try:
            resp_schema = post['responses']['200']['content']['application/json']['schema']
            result_schema = resp_schema['properties']['result']
        except Exception:
            continue

        example_result = by_op[op_id].get('response_success', {}).get('result')
        inferred = infer_schema(example_result)
        if not inferred:
            continue

        if is_weak_result_schema(result_schema) or not loosely_matches(result_schema, example_result):
            resp_schema['properties']['result'] = merge_schema(result_schema, inferred)
            tightened += 1

    SPEC_PATH.write_text(yaml.safe_dump(spec, allow_unicode=True, sort_keys=False), encoding='utf-8')
    print(f'Tightened {tightened} result schemas from examples (scanned {scanned} operations).')


if __name__ == '__main__':
    main()
