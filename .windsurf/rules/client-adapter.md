# Client Adapter Rule (Windsurf)

Scope: `client/python/**`, `client/ts/**`

- Treat operation maps as source for `upstreamPath` + `upstreamMethod`.
- Build JSON-RPC envelope exactly: `jsonrpc`, `method`, `params`, optional `id/user`.
- Never execute virtual `/rpc/*` paths against real API host.
