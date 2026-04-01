# LLM Usage Rules

## Purpose
Help LLM agents choose correct API actions and generate runnable code.

## Which spec to use
- Planning / intent-to-operation mapping: `spec/openapi.llm-projection.yaml`
- Real execution / client generation: `spec/openapi.transport.yaml`

## Execution algorithm
1. Select operation in projection spec by intent.
2. Read `x-sweb-upstream-path` and `x-sweb-upstream-method`.
3. Build JSON-RPC request for transport spec:
   - `jsonrpc: "2.0"`
   - `method: <x-sweb-upstream-method>`
   - `params: <validated params>`
4. Send HTTP POST to `<server-url><x-sweb-upstream-path>`.
5. Parse envelope:
   - success: `result`
   - error: `error.code`, `error.message`, `error.data`

## Auth flow
1. Get token via `POST /notAuthorized/`, method `getToken`.
2. Reuse token in `Authorization: Bearer <token>`.
3. If error matches expired session (`-32603`, message contains `Время сеанса истекло`) -> refresh token and retry once.

## Safety rules
- Never fabricate methods.
- Never silently drop required params.
- Preserve full upstream path for nested modules.
- Validate param types against schema before sending request.

## Retry policy
- Retry network errors with backoff.
- Do not blind-retry application errors (`-32601`, validation errors).
