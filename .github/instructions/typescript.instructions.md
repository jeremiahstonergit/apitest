---
applyTo: "client/ts/**"
---

TypeScript work in this repo should keep transport adapter deterministic.

Rules:
- Use `client/ts/transport.ts` for real API execution.
- Do not treat `spec/openapi.llm-projection.yaml` as executable endpoints.
- Always map operationId -> upstreamPath/upstreamMethod via generated operation map.
- Keep JSON-RPC payload shape strict.
- If schema/ops changed, regenerate and validate:
  - `python scripts/build_mvp.py --limit 120`
  - `python scripts/tighten_results_from_examples.py`
  - `python scripts/validate_mvp.py`
