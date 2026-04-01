# AGENTS.md — Instructions for Codex/LLM agents

This project is an LLM-first adapter layer for SpaceWeb JSON-RPC API.

## Ground truth
- Raw source of truth: `notes/raw/schema/**/openrpc*.json`
- Inventory: `notes/inventory.methods.json`
- Build script: `scripts/build_mvp.py`

## Specs in this repo
1) `spec/openapi.llm-projection.yaml`
- Virtual semantic projection for agent planning and tool selection.
- Paths like `/rpc/...` are NOT directly executable against `api.sweb.ru`.

2) `spec/openapi.transport.yaml`
- Executable transport contract for real HTTP requests to `https://api.sweb.ru`.
- Uses JSON-RPC envelope in request body.

## Auth
- Get token via `POST /notAuthorized/` with method `getToken`.
- For protected endpoints use `Authorization: Bearer <token>`.
- Details: `auth/AUTH.md`, machine format: `auth/auth.machine.json`.

## Mandatory rules
- Do NOT invent fields or methods not present in raw OpenRPC schemas.
- For nested namespaces, keep full upstream path (e.g. `/domains/bonus/`, `/monitoring/checks/`).
- If there is conflict between projection and raw schemas, raw schemas win.
- For runnable code generation, prefer `openapi.transport.yaml`.
- For planning/selecting operations, prefer `openapi.llm-projection.yaml`.
