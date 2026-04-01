# SpaceWeb API Rules (Windsurf)

- Source of truth for API shape: `notes/raw/schema/**/openrpc*.json`
- Virtual planning spec: `spec/openapi.llm-projection.yaml`
- Executable spec: `spec/openapi.transport.yaml`
- Never call virtual `/rpc/*` paths against `api.sweb.ru`.
- For real calls use JSON-RPC envelope on upstream path from `x-sweb-upstream-path`.
- Auth flow:
  1) `POST /notAuthorized/` method `getToken`
  2) `Authorization: Bearer <token>` for protected methods
- Run before commit:
  - `python scripts/build_mvp.py --limit 120`
  - `python scripts/validate_mvp.py`
