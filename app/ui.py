"""HTML helpers for the FastAPI control plane."""

from __future__ import annotations

import html
from typing import Any

from fastapi.responses import HTMLResponse

STYLE = """
:root{color-scheme:dark;--bg:#0b1020;--panel:#11182c;--muted:#8fa3c7;--text:#edf4ff;--brand:#60a5fa;--ok:#34d399;--warn:#fbbf24;--bad:#fb7185}*{box-sizing:border-box}body{margin:0;font-family:Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif;background:radial-gradient(circle at top left,#1d4ed833,transparent 34rem),var(--bg);color:var(--text)}main{max-width:1180px;margin:0 auto;padding:32px 20px 64px}.hero{display:flex;justify-content:space-between;gap:24px;align-items:flex-start;margin-bottom:28px}.badge{display:inline-flex;gap:8px;align-items:center;border:1px solid #2a3a5e;background:#0f172a;padding:8px 12px;border-radius:999px;color:#bfdbfe;font-size:14px}h1{font-size:clamp(32px,5vw,58px);line-height:1;margin:16px 0 12px;letter-spacing:-.04em}.lead{color:var(--muted);font-size:18px;max-width:760px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px}.card{border:1px solid #253653;background:linear-gradient(180deg,#16213acc,#10172acc);border-radius:24px;padding:22px;box-shadow:0 20px 60px #0006}.card h2,.card h3{margin-top:0}.muted{color:var(--muted)}.pill{display:inline-block;border-radius:999px;padding:5px 10px;background:#1e293b;color:#bfdbfe;font-size:12px;margin:2px}.actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:14px}.btn,button{border:0;border-radius:14px;background:linear-gradient(135deg,#3b82f6,#06b6d4);color:white;padding:10px 14px;font-weight:700;cursor:pointer;text-decoration:none}.btn.secondary{background:#1f2a44;color:#cfe2ff;border:1px solid #33476d}input,textarea,select{width:100%;border:1px solid #314262;background:#0b1222;color:var(--text);border-radius:14px;padding:11px;margin:6px 0 12px}textarea{min-height:110px;font-family:ui-monospace,Menlo,monospace}.status-ok{color:var(--ok)}.status-failed{color:var(--bad)}table{width:100%;border-collapse:collapse}td,th{border-bottom:1px solid #263653;padding:10px;text-align:left;vertical-align:top}code{color:#bfdbfe}.section{margin-top:26px}.small{font-size:13px}.split{display:grid;grid-template-columns:1.2fr .8fr;gap:18px}@media(max-width:850px){.hero,.split{display:block}.card{margin-bottom:16px}}
"""


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def render_page(content: str) -> HTMLResponse:
    return HTMLResponse(
        f"""<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>SpaceWeb Control Plane</title><style>{STYLE}</style></head><body><main><div class="hero"><div><span class="badge">● Knative-ready FastAPI</span><h1>Панель управления инфраструктурой SpaceWeb</h1><p class="lead">Запускайте Python-скрипты из Git-репозитория вручную или по расписанию. UI построен для serverless-контейнера: порт берётся из переменной <code>PORT</code>, есть health-check и лёгкий in-process scheduler.</p></div></div>{content}</main></body></html>"""
    )
