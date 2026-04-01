# Claude Code Project Notes

This repo uses a two-layer API representation:

1) `spec/openapi.llm-projection.yaml`
- Virtual semantic layer for operation planning.
- Not directly executable against `https://api.sweb.ru`.

2) `spec/openapi.transport.yaml`
- Real executable transport layer for JSON-RPC over HTTP POST.

## Critical rules
- Do not invent methods/fields absent in `notes/raw/schema/**/openrpc*.json`.
- Keep full nested upstream paths (e.g. `/domains/bonus/`, `/monitoring/checks/`).
- For runnable integrations prefer `client/python/transport.py` or `client/ts/transport.ts`.

## Auth
- Token: `POST /notAuthorized/` with method `getToken`.
- Protected calls require `Authorization: Bearer <token>`.
