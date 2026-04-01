# Copilot Coding Agent Instructions

## Architecture
- `spec/openapi.llm-projection.yaml` = virtual planning layer.
- `spec/openapi.transport.yaml` = executable JSON-RPC transport contract.

## Do / Don't
- DO use `x-sweb-upstream-path` + `x-sweb-upstream-method` for real calls.
- DO keep JSON-RPC envelope: `jsonrpc`, `method`, `params`.
- DO use adapters in `client/python/transport.py` or `client/ts/transport.ts`.
- DON'T call virtual `/rpc/*` paths on `https://api.sweb.ru`.
- DON'T invent methods or params not present in raw OpenRPC schemas.

## Validation commands
```bash
python scripts/build_mvp.py --limit 120
python scripts/validate_mvp.py
```
