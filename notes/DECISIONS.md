# Decisions (draft)

## Target format for LLM-first OpenAPI

Because source API is JSON-RPC over HTTP POST, we need a stable mapping to OpenAPI paths.

### Proposed mapping
- Source transport: `POST https://api.sweb.ru/<object>/` with body `{jsonrpc, method, params, id, user?}`.
- OpenAPI representation:
  - one endpoint per RPC method:
    - `POST /rpc/<object>/<method>`
  - request body:
    - `params` object only (business params)
    - optional `id`, `user` fields where relevant
  - response body:
    - normalized envelope: `{ result, error, id, jsonrpc, version }`
  - extension fields:
    - `x-sweb-upstream-path`: `/domains/`
    - `x-sweb-upstream-method`: `move`
    - `x-sweb-transport`: `jsonrpc-over-http`

### Auth
- Token retrieval RPC:
  - `POST /notAuthorized/` with RPC method `getToken`.
- For most methods: `Authorization: Bearer <token>`.
- OpenAPI security scheme: `http` + `bearer`.

### Why this mapping
- Keeps one-operation-per-action for LLM tool selection.
- Avoids giant `oneOf` on single `/domains/` endpoint.
- Preserves traceability to original API via `x-sweb-*` fields.

## Open questions
- Keep `/rpc/<object>/<method>` prefix or use `/<object>/<method>`?
- Do we include raw JSON-RPC envelope in every request/response schema, or hide envelope and keep only business payloads?
- Should we generate both representations (`strict-rpc` and `llm-friendly`) as two spec files?
