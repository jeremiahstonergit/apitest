"""SpaceWeb JSON-RPC transport adapter (RC draft).

Purpose:
- Bridge LLM projection operations to real JSON-RPC HTTP endpoints.
- Use `spec/openapi.llm-projection.yaml` as operation map.

Example:
    from transport import SwebTransportClient

    c = SwebTransportClient(token='...')
    data = c.call_by_operation('domains_bonus_getList', params={})
    print(data['result'])
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
import json
import requests
import yaml


DEFAULT_SERVER = 'https://api.sweb.ru'


class SwebApiError(RuntimeError):
    def __init__(self, code: int, message: str, data: Any = None):
        super().__init__(f'Sweb API error {code}: {message}')
        self.code = code
        self.message = message
        self.data = data


@dataclass
class OperationMeta:
    operation_id: str
    upstream_path: str
    upstream_method: str


class SwebTransportClient:
    def __init__(
        self,
        token: Optional[str] = None,
        server: str = DEFAULT_SERVER,
        projection_spec_path: Optional[str] = None,
        timeout_sec: int = 30,
    ):
        self.token = token
        self.server = server.rstrip('/')
        self.timeout_sec = timeout_sec

        if projection_spec_path is None:
            root = Path(__file__).resolve().parents[2]
            projection_spec_path = str(root / 'spec' / 'openapi.llm-projection.yaml')
        self._ops = self._load_ops(projection_spec_path)

    @staticmethod
    def _load_ops(path: str) -> Dict[str, OperationMeta]:
        spec = yaml.safe_load(Path(path).read_text(encoding='utf-8'))
        out: Dict[str, OperationMeta] = {}
        for _, item in (spec.get('paths') or {}).items():
            post = (item or {}).get('post')
            if not post:
                continue
            op_id = post.get('operationId')
            up_path = post.get('x-sweb-upstream-path')
            up_method = post.get('x-sweb-upstream-method')
            if not (op_id and up_path and up_method):
                continue
            out[op_id] = OperationMeta(
                operation_id=op_id,
                upstream_path=up_path,
                upstream_method=up_method,
            )
        return out

    def get_token(self, login: str, password: str, req_id: Optional[str] = None) -> str:
        body = {
            'jsonrpc': '2.0',
            'method': 'getToken',
            'params': {'login': login, 'password': password},
        }
        if req_id is not None:
            body['id'] = req_id

        resp = self._post('/notAuthorized/', body, with_auth=False)
        token = resp.get('result')
        if not token or not isinstance(token, str):
            raise RuntimeError('Token was not returned in result')
        self.token = token
        return token

    def call_by_operation(
        self,
        operation_id: str,
        params: Dict[str, Any],
        req_id: Optional[str] = None,
        user: Optional[str] = None,
    ) -> Dict[str, Any]:
        meta = self._ops.get(operation_id)
        if not meta:
            raise KeyError(f'Unknown operationId: {operation_id}')

        body: Dict[str, Any] = {
            'jsonrpc': '2.0',
            'method': meta.upstream_method,
            'params': params or {},
        }
        if req_id is not None:
            body['id'] = req_id
        if user is not None:
            body['user'] = user

        with_auth = not (meta.upstream_path == '/notAuthorized/' and meta.upstream_method == 'getToken')
        return self._post(meta.upstream_path, body, with_auth=with_auth)

    def _post(self, path: str, body: Dict[str, Any], with_auth: bool) -> Dict[str, Any]:
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': 'application/json',
        }
        if with_auth:
            if not self.token:
                raise RuntimeError('Auth token is required but not set')
            headers['Authorization'] = f'Bearer {self.token}'

        url = f"{self.server}{path}"
        r = requests.post(url, headers=headers, data=json.dumps(body, ensure_ascii=False), timeout=self.timeout_sec)
        r.raise_for_status()
        payload = r.json()

        err = payload.get('error')
        if isinstance(err, dict):
            raise SwebApiError(err.get('code', -1), err.get('message', 'Unknown error'), err.get('data'))
        return payload
