---
applyTo: "client/python/**,scripts/**"
---

Python work in this repo must follow SpaceWeb transport architecture.

Rules:
- Use `client/python/transport.py` as the execution path to real API.
- Never call virtual `/rpc/*` paths on `https://api.sweb.ru`.
- Preserve JSON-RPC envelope (`jsonrpc`, `method`, `params`).
- Keep method/path mapping from `x-sweb-upstream-*` fields.
- Before finishing changes, run:
  - `python scripts/build_mvp.py --limit 120`
  - `python scripts/tighten_results_from_examples.py`
  - `python scripts/validate_mvp.py`
