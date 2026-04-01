import json
import glob
import argparse
import re
from pathlib import Path
from urllib.parse import urlparse


def resolve_root(explicit_root: str | None = None) -> Path:
    if explicit_root:
        return Path(explicit_root).resolve()
    # default: project root = parent of scripts/
    return Path(__file__).resolve().parent.parent


DEFAULT_METHOD_LIMIT = None


def load_docs(raw_dir: Path):
    docs = []
    for fp in sorted(glob.glob(str(raw_dir / '**' / 'openrpc*.json'), recursive=True)):
        with open(fp, encoding='utf-8') as f:
            docs.append((Path(fp), json.load(f)))
    return docs


def upstream_path(doc_path: Path, doc: dict) -> str:
    servers = doc.get('servers') or []
    if servers and isinstance(servers[0], dict):
        u = (servers[0].get('url') or '').strip()
        if u:
            p = urlparse(u).path or '/'
            if not p.startswith('/'):
                p = '/' + p
            if not p.endswith('/'):
                p += '/'
            return p
    # fallback
    seg = doc_path.stem.replace('openrpc.', '')
    return f'/{seg}/'


def primitive_from_ref(ref: str):
    key = ref.split('/')[-1]
    return {
        'String': {'type': 'string'},
        'Integer': {'type': 'integer'},
        'Boolean': {'type': 'boolean'},
        'Float': {'type': 'number'},
        'Number': {'type': 'number'},
        'Array': {'type': 'array', 'items': {}},
        'Object': {'type': 'object', 'additionalProperties': True},
    }.get(key)


def resolve_schema(doc: dict, schema_obj: dict):
    if not isinstance(schema_obj, dict):
        return {'type': 'object', 'additionalProperties': True}

    if '$ref' in schema_obj:
        ref = schema_obj['$ref']
        p = primitive_from_ref(ref)
        if p:
            return p
        if ref.startswith('#/components/schemas/'):
            key = ref.split('/')[-1]
            target = ((doc.get('components') or {}).get('schemas') or {}).get(key)
            if isinstance(target, dict):
                # OpenRPC schemas are close enough to JSON schema
                t = target.get('type')
                if t:
                    out = {'type': t}
                    if t == 'object':
                        props = target.get('properties') or {}
                        out['properties'] = {k: resolve_schema(doc, v) for k, v in props.items()}
                        if 'required' in target:
                            out['required'] = target['required']
                        out['additionalProperties'] = target.get('additionalProperties', True)
                    if t == 'array':
                        out['items'] = resolve_schema(doc, target.get('items', {}))
                    if 'enum' in target:
                        out['enum'] = target['enum']
                    return out
            return {'type': 'object', 'additionalProperties': True}
        if ref.startswith('#/components/contentDescriptors/'):
            key = ref.split('/')[-1]
            cd = ((doc.get('components') or {}).get('contentDescriptors') or {}).get(key, {})
            return resolve_schema(doc, cd.get('schema', {}))
        return {'type': 'object', 'additionalProperties': True}

    t = schema_obj.get('type')
    if t == 'object':
        props = schema_obj.get('properties') or {}
        out = {
            'type': 'object',
            'properties': {k: resolve_schema(doc, v) for k, v in props.items()},
            'additionalProperties': schema_obj.get('additionalProperties', True),
        }
        if 'required' in schema_obj:
            out['required'] = schema_obj['required']
        return out
    if t == 'array':
        return {'type': 'array', 'items': resolve_schema(doc, schema_obj.get('items', {}))}

    out = {}
    if t:
        out['type'] = t
    if 'enum' in schema_obj:
        out['enum'] = schema_obj['enum']
    if 'description' in schema_obj:
        out['description'] = schema_obj['description']
    return out or {'type': 'object', 'additionalProperties': True}


def is_nullable_schema(schema: dict) -> bool:
    if not isinstance(schema, dict):
        return False
    if schema.get('nullable') is True:
        return True
    t = schema.get('type')
    return isinstance(t, list) and 'null' in t


def value_matches_schema(schema: dict, v) -> bool:
    if v is None:
        return is_nullable_schema(schema)
    t = (schema or {}).get('type')
    if isinstance(t, list):
        return any(value_matches_schema({'type': tt, **{k: vv for k, vv in schema.items() if k != 'type'}}, v) for tt in t)
    if t == 'integer':
        return isinstance(v, int) and not isinstance(v, bool)
    if t == 'number':
        return isinstance(v, (int, float)) and not isinstance(v, bool)
    if t == 'boolean':
        return isinstance(v, bool)
    if t == 'string':
        return isinstance(v, str)
    if t == 'array':
        return isinstance(v, list)
    if t == 'object':
        return isinstance(v, dict)
    return True


def coerce_value(schema: dict, v):
    t = (schema or {}).get('type')
    if v is None:
        return None
    try:
        if t == 'integer':
            if isinstance(v, str):
                s = v.strip()
                if s == '':
                    return None
                m = re.search(r'-?\d+', s.replace(',', '.'))
                if m:
                    return int(m.group(0))
            return int(v)
        if t == 'number':
            if isinstance(v, str):
                s = v.strip().replace(',', '.')
                m = re.search(r'-?\d+(?:\.\d+)?', s)
                if m:
                    return float(m.group(0))
            return float(v)
        if t == 'boolean':
            if isinstance(v, bool):
                return v
            if isinstance(v, str):
                return v.lower() in ('1', 'true', 'yes', 'y')
        if t == 'string':
            return str(v)
        if t == 'array':
            if isinstance(v, list):
                return v
            return [v]
        if t == 'object':
            if isinstance(v, dict):
                return v
            return {}
    except Exception:
        return v
    return v


def coerce_result_to_schema(schema: dict, value):
    if value is None:
        return None
    if not isinstance(schema, dict) or not schema:
        return value
    t = schema.get('type')
    if isinstance(t, list):
        for tt in t:
            if tt == 'null':
                continue
            coerced = coerce_result_to_schema({'type': tt, **{k: v for k, v in schema.items() if k != 'type'}}, value)
            if value_matches_schema({'type': tt, **{k: v for k, v in schema.items() if k != 'type'}}, coerced):
                return coerced
        return value
    if t in ('string', 'integer', 'number', 'boolean', 'array', 'object'):
        if t == 'array':
            arr = value if isinstance(value, list) else [value]
            item_schema = schema.get('items') or {}
            return [coerce_result_to_schema(item_schema, x) for x in arr]
        if t == 'object':
            if not isinstance(value, dict):
                return {}
            props = schema.get('properties') or {}
            out = {}
            for k, v in value.items():
                if k in props:
                    out[k] = coerce_result_to_schema(props[k], v)
                else:
                    out[k] = v
            return out
        return coerce_value(schema, value)
    return value



def placeholder_value_for_schema(schema: dict):
    if not isinstance(schema, dict):
        return None
    t = schema.get('type')
    if isinstance(t, list):
        for tt in t:
            if tt != 'null':
                return placeholder_value_for_schema({'type': tt, **{k: v for k, v in schema.items() if k != 'type'}})
        return None
    if schema.get('nullable') is True:
        return None
    if t == 'integer':
        return 0
    if t == 'number':
        return 0
    if t == 'boolean':
        return False
    if t == 'string':
        enum = schema.get('enum')
        return enum[0] if enum else ''
    if t == 'array':
        return []
    if t == 'object':
        out = {}
        for key in schema.get('required') or []:
            out[key] = placeholder_value_for_schema((schema.get('properties') or {}).get(key, {}))
        return out
    return None

def op_id_from_path_and_method(upstream: str, method: str):
    seg = upstream.strip('/').replace('/', '_').replace('-', '_')
    return f'{seg}_{method}'.strip('_')


def build(root: Path, target_methods: int | None = DEFAULT_METHOD_LIMIT):
    raw = root / 'notes' / 'raw' / 'schema'
    out_spec_llm = root / 'spec' / 'openapi.llm-projection.yaml'
    out_spec_transport = root / 'spec' / 'openapi.transport.yaml'
    out_ex = root / 'examples' / 'examples.jsonl'
    out_methods = root / 'notes' / 'mvp.methods.md'
    out_py_ops = root / 'client' / 'python' / 'operations.generated.json'
    out_ts_ops = root / 'client' / 'ts' / 'operations.generated.json'

    docs = load_docs(raw)
    paths_llm = {}
    paths_transport = {}
    examples_lines = []
    selected = []

    c = 0
    for doc_path, doc in docs:
        up = upstream_path(doc_path, doc)  # e.g. /domains/bonus/
        methods = doc.get('methods') or []
        for m in methods:
            if target_methods is not None and c >= target_methods:
                break
            mname = m.get('name')
            if not mname:
                continue

            op_id = op_id_from_path_and_method(up, mname)
            llm_path = '/rpc/' + up.strip('/') + f'/{mname}'
            real_path = up

            params_schema = {'type': 'object', 'properties': {}, 'additionalProperties': False}
            params_required = []
            param_types = {}
            for p in (m.get('params') or []):
                pname = p.get('name')
                if not pname:
                    continue
                ps = resolve_schema(doc, p.get('schema', {}))
                if p.get('description'):
                    ps.setdefault('description', p['description'])
                params_schema['properties'][pname] = ps
                param_types[pname] = ps
                if p.get('required'):
                    params_required.append(pname)
            if params_required:
                params_schema['required'] = params_required

            result_schema = {'type': 'object', 'additionalProperties': True}
            if isinstance(m.get('result'), dict):
                result_schema = resolve_schema(doc, m['result'])

            response_envelope = {
                'type': 'object',
                'properties': {
                    'jsonrpc': {'type': 'string', 'example': '2.0'},
                    'id': {'type': 'string'},
                    'version': {'type': 'string'},
                    'result': result_schema,
                    'error': {'$ref': '#/components/schemas/RpcError'},
                },
                'additionalProperties': True,
            }

            common_ext = {
                'x-sweb-upstream-path': up,
                'x-sweb-upstream-method': mname,
                'x-sweb-transport': 'jsonrpc-over-http',
            }

            llm_op = {
                'tags': [up.strip('/').split('/')[0]],
                'summary': m.get('description') or m.get('summary') or mname,
                'operationId': op_id,
                **common_ext,
                'requestBody': {
                    'required': True,
                    'content': {
                        'application/json': {
                            'schema': {
                                'type': 'object',
                                'properties': {
                                    'params': params_schema,
                                    'id': {'type': 'string'},
                                    'user': {'type': 'string'},
                                },
                                'required': ['params'],
                                'additionalProperties': False,
                            }
                        }
                    }
                },
                'responses': {
                    '200': {
                        'description': 'JSON-RPC response envelope',
                        'content': {'application/json': {'schema': response_envelope}},
                    }
                },
                'security': [{'bearerAuth': []}],
            }

            transport_op = {
                'tags': [up.strip('/').split('/')[0]],
                'summary': m.get('description') or m.get('summary') or mname,
                'operationId': op_id + '_transport',
                **common_ext,
                'requestBody': {
                    'required': True,
                    'content': {
                        'application/json': {
                            'schema': {
                                'type': 'object',
                                'properties': {
                                    'jsonrpc': {'type': 'string', 'enum': ['2.0']},
                                    'method': {'type': 'string', 'enum': [mname]},
                                    'params': params_schema,
                                    'id': {'type': 'string'},
                                    'user': {'type': 'string'},
                                },
                                'required': ['jsonrpc', 'method', 'params'],
                                'additionalProperties': False,
                            }
                        }
                    }
                },
                'responses': {
                    '200': {
                        'description': 'JSON-RPC response envelope',
                        'content': {'application/json': {'schema': response_envelope}},
                    }
                },
                'security': [{'bearerAuth': []}],
            }

            # auth bypass for notAuthorized.getToken
            if up == '/notAuthorized/' and mname == 'getToken':
                llm_op['security'] = []
                transport_op['security'] = []

            paths_llm[llm_path] = {'post': llm_op}
            if real_path not in paths_transport:
                paths_transport[real_path] = {
                    'post': {
                        'tags': [up.strip('/').split('/')[0]],
                        'summary': f'RPC object endpoint {up}',
                        'operationId': op_id + '_object',
                        'x-sweb-upstream-path': up,
                        'x-sweb-transport': 'jsonrpc-over-http',
                        'requestBody': {
                            'required': True,
                            'content': {
                                'application/json': {
                                    'schema': {
                                        'type': 'object',
                                        'properties': {
                                            'jsonrpc': {'type': 'string', 'enum': ['2.0']},
                                            'method': {'type': 'string'},
                                            'params': {'type': 'object', 'additionalProperties': True},
                                            'id': {'type': 'string'},
                                            'user': {'type': 'string'},
                                        },
                                        'required': ['jsonrpc', 'method', 'params'],
                                        'additionalProperties': False,
                                    }
                                }
                            }
                        },
                        'responses': {
                            '200': {
                                'description': 'JSON-RPC response (generic envelope for object endpoint)',
                                'content': {
                                    'application/json': {
                                        'schema': {
                                            'type': 'object',
                                            'properties': {
                                                'jsonrpc': {'type': 'string', 'example': '2.0'},
                                                'id': {'type': 'string'},
                                                'version': {'type': 'string'},
                                                'result': {'description': 'Method-specific payload', 'nullable': True},
                                                'error': {'$ref': '#/components/schemas/RpcError'},
                                            },
                                            'additionalProperties': True,
                                        }
                                    }
                                },
                            }
                        },
                        'security': [] if (up == '/notAuthorized/') else [{'bearerAuth': []}],
                    }
                }

            selected.append((up, mname, llm_path, m.get('description') or ''))
            c += 1

            # examples
            ex_params = {}
            ex_result = {}
            ex = (m.get('examples') or [None])[0]
            if isinstance(ex, dict):
                method_params = m.get('params') or []
                for i, pref in enumerate(ex.get('params') or []):
                    if not (isinstance(pref, dict) and '$ref' in pref):
                        continue
                    key = pref['$ref'].split('/')[-1]
                    exv = ((doc.get('components') or {}).get('examples') or {}).get(key)
                    if not isinstance(exv, dict):
                        continue
                    # Prefer canonical param name from method schema by position; fallback to example key/name
                    pname = method_params[i].get('name') if i < len(method_params) else exv.get('name', key)
                    val = exv.get('value')
                    schema = param_types.get(pname, {})
                    coerced = coerce_value(schema, val)

                    # If positional mapping clearly mismatched, retry with explicit example name
                    ex_name = exv.get('name')
                    if ex_name in param_types and not value_matches_schema(schema, coerced):
                        pname = ex_name
                        schema = param_types.get(pname, {})
                        coerced = coerce_value(schema, val)
                    # avoid null noise for non-nullable optional params
                    if coerced is None and not is_nullable_schema(schema) and pname not in params_required:
                        continue
                    # if still mismatched and optional, drop from example rather than poisoning training signal
                    if not value_matches_schema(schema, coerced) and pname not in params_required:
                        continue
                    ex_params[pname] = coerced
                rref = (ex.get('result') or {}).get('$ref') if isinstance(ex.get('result'), dict) else None
                if rref:
                    rk = rref.split('/')[-1]
                    exr = ((doc.get('components') or {}).get('examples') or {}).get(rk)
                    if isinstance(exr, dict):
                        ex_result = coerce_result_to_schema(result_schema, exr.get('value', {}))

            for req_name in params_required:
                if req_name not in ex_params:
                    ex_params[req_name] = placeholder_value_for_schema(param_types.get(req_name, {}))

            examples_lines.append(json.dumps({
                'operationId': op_id,
                'upstream': {'path': up, 'method': mname},
                'request': {'params': ex_params},
                'response_success': {'result': ex_result},
                'response_error': {'error': {'code': -32603, 'message': 'Ошибка выполнения метода'}},
            }, ensure_ascii=False))

        if target_methods is not None and c >= target_methods:
            break

    # Ensure auth flow is represented as first-class operation
    token_llm_path = '/rpc/notAuthorized/getToken'
    if token_llm_path not in paths_llm:
        paths_llm[token_llm_path] = {
            'post': {
                'tags': ['notAuthorized'],
                'summary': 'Получение токена для взаимодействия с API',
                'operationId': 'notAuthorized_getToken',
                'x-sweb-upstream-path': '/notAuthorized/',
                'x-sweb-upstream-method': 'getToken',
                'x-sweb-transport': 'jsonrpc-over-http',
                'requestBody': {
                    'required': True,
                    'content': {
                        'application/json': {
                            'schema': {
                                'type': 'object',
                                'properties': {
                                    'params': {
                                        'type': 'object',
                                        'properties': {
                                            'login': {'type': 'string'},
                                            'password': {'type': 'string'},
                                        },
                                        'required': ['login', 'password'],
                                        'additionalProperties': False,
                                    },
                                    'id': {'type': 'string'},
                                },
                                'required': ['params'],
                                'additionalProperties': False,
                            }
                        }
                    }
                },
                'responses': {
                    '200': {
                        'description': 'JSON-RPC response envelope',
                        'content': {
                            'application/json': {
                                'schema': {
                                    'type': 'object',
                                    'properties': {
                                        'jsonrpc': {'type': 'string', 'example': '2.0'},
                                        'id': {'type': 'string'},
                                        'version': {'type': 'string'},
                                        'result': {'type': 'string', 'description': 'Auth token'},
                                        'error': {'$ref': '#/components/schemas/RpcError'},
                                    },
                                    'additionalProperties': True,
                                }
                            }
                        }
                    }
                },
                'security': [],
            }
        }

    paths_transport['/notAuthorized/'] = {
        'post': {
            'tags': ['notAuthorized'],
            'summary': 'JSON-RPC endpoint for public auth methods',
            'operationId': 'notAuthorized_object',
            'x-sweb-upstream-path': '/notAuthorized/',
            'x-sweb-transport': 'jsonrpc-over-http',
            'requestBody': {
                'required': True,
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'jsonrpc': {'type': 'string', 'enum': ['2.0']},
                                'method': {'type': 'string'},
                                'params': {'type': 'object', 'additionalProperties': True},
                                'id': {'type': 'string'},
                            },
                            'required': ['jsonrpc', 'method', 'params'],
                            'additionalProperties': False,
                        }
                    }
                }
            },
            'responses': {
                '200': {
                    'description': 'JSON-RPC response',
                    'content': {'application/json': {'schema': {'type': 'object', 'additionalProperties': True}}},
                }
            },
            'security': [],
        }
    }

    spec_common_components = {
        'securitySchemes': {
            'bearerAuth': {'type': 'http', 'scheme': 'bearer', 'bearerFormat': 'Token'}
        },
        'schemas': {
            'RpcError': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer'},
                    'message': {'type': 'string'},
                    'data': {'type': 'array', 'items': {}},
                },
                'required': ['code', 'message'],
                'additionalProperties': True,
            }
        }
    }

    spec_llm = {
        'openapi': '3.0.3',
        'info': {
            'title': 'SpaceWeb API (LLM projection)',
            'version': '0.3.0-mvp',
            'description': 'Virtual LLM-friendly projection. Not directly executable against api.sweb.ru.',
        },
        'servers': [{'url': 'https://virtual.sweb.local', 'description': 'Virtual server for LLM planning'}],
        'security': [{'bearerAuth': []}],
        'paths': paths_llm,
        'components': spec_common_components,
    }

    spec_transport = {
        'openapi': '3.0.3',
        'info': {
            'title': 'SpaceWeb API (transport contract)',
            'version': '0.3.0-mvp',
            'description': 'Executable contract for JSON-RPC over HTTP POST endpoints.',
        },
        'servers': [{'url': 'https://api.sweb.ru'}],
        'security': [{'bearerAuth': []}],
        'paths': paths_transport,
        'components': spec_common_components,
    }

    try:
        import yaml
        with open(out_spec_llm, 'w', encoding='utf-8') as f:
            yaml.safe_dump(spec_llm, f, allow_unicode=True, sort_keys=False)
        with open(out_spec_transport, 'w', encoding='utf-8') as f:
            yaml.safe_dump(spec_transport, f, allow_unicode=True, sort_keys=False)
    except Exception:
        with open(out_spec_llm, 'w', encoding='utf-8') as f:
            json.dump(spec_llm, f, ensure_ascii=False, indent=2)
        with open(out_spec_transport, 'w', encoding='utf-8') as f:
            json.dump(spec_transport, f, ensure_ascii=False, indent=2)

    # Ensure auth example exists for first-run agent flow
    if not any('"operationId": "notAuthorized_getToken"' in l for l in examples_lines):
        examples_lines.append(json.dumps({
            'operationId': 'notAuthorized_getToken',
            'upstream': {'path': '/notAuthorized/', 'method': 'getToken'},
            'request': {'params': {'login': '<LOGIN>', 'password': '<PASSWORD>'}},
            'response_success': {'result': '<TOKEN>'},
            'response_error': {'error': {'code': -32603, 'message': 'Ошибка выполнения метода'}},
        }, ensure_ascii=False))

    with open(out_ex, 'w', encoding='utf-8') as f:
        for line in examples_lines:
            f.write(line + '\n')

    with open(out_methods, 'w', encoding='utf-8') as f:
        f.write('# MVP included methods\n\n')
        f.write(f'Total: **{len(selected)}**\n\n')
        for up, mname, p, desc in selected:
            f.write(f'- `{p}` ← `{up}{mname}` — {desc}\n')


    # generated operation maps for adapters
    op_map = {}
    for _, item in paths_llm.items():
        post = (item or {}).get('post') or {}
        op_id = post.get('operationId')
        up_path = post.get('x-sweb-upstream-path')
        up_method = post.get('x-sweb-upstream-method')
        if op_id and up_path and up_method:
            op_map[op_id] = {
                'operationId': op_id,
                'upstreamPath': up_path,
                'upstreamMethod': up_method,
            }

    with open(out_py_ops, 'w', encoding='utf-8') as f:
        json.dump(op_map, f, ensure_ascii=False, indent=2, sort_keys=True)
    with open(out_ts_ops, 'w', encoding='utf-8') as f:
        json.dump(op_map, f, ensure_ascii=False, indent=2, sort_keys=True)

    print(f'LLM spec: {out_spec_llm}')
    print(f'Transport spec: {out_spec_transport}')
    print(f'Examples: {out_ex} ({len(examples_lines)} lines)')
    print(f'Operation maps: {out_py_ops}, {out_ts_ops} ({len(op_map)} operations)')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build SpaceWeb LLM/transport OpenAPI MVP artifacts')
    parser.add_argument('--root', help='Project root (default: parent of scripts/)')
    parser.add_argument('--limit', type=int, default=None, help='Max methods to include. Omit for all discovered methods.')
    args = parser.parse_args()

    build(resolve_root(args.root), args.limit)
