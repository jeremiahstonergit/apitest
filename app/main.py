"""FastAPI control plane for SpaceWeb infrastructure automation on Knative Serving."""

from __future__ import annotations

import asyncio
import html
import json
import os
import secrets
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Form, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse, RedirectResponse

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / 'automation' / 'tasks.registry.json'
DATA_DIR = Path(os.getenv('SWEB_AUTOMATION_DATA_DIR', ROOT / '.runtime'))
SCHEDULES_PATH = DATA_DIR / 'schedules.json'
MAX_LOGS = int(os.getenv('SWEB_AUTOMATION_MAX_LOGS', '50'))
CONTROL_PLANE_USER = os.getenv('CONTROL_PLANE_USER', 'shashkin')
CONTROL_PLANE_PASSWORD = os.getenv('CONTROL_PLANE_PASSWORD', 'dumbilla')


app = FastAPI(
    title='SpaceWeb Infrastructure Control Plane',
    description='Web UI and lightweight scheduler for repository-managed Python automation scripts.',
    version='0.1.0',
)


@dataclass
class TaskDef:
    id: str
    title: str
    service: str
    description: str
    script: str
    default_params: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScheduleDef:
    id: str
    task_id: str
    title: str
    interval_minutes: int
    params: dict[str, Any]
    enabled: bool = True
    next_run_at: str | None = None
    last_run_at: str | None = None
    last_status: str | None = None


TASKS: dict[str, TaskDef] = {}
SCHEDULES: dict[str, ScheduleDef] = {}
RUN_LOGS: list[dict[str, Any]] = []
SCHEDULER_TASK: asyncio.Task | None = None
SECURITY = HTTPBasic()



STYLE = """
:root{color-scheme:dark;--bg:#0b1020;--panel:#11182c;--muted:#8fa3c7;--text:#edf4ff;--brand:#60a5fa;--ok:#34d399;--warn:#fbbf24;--bad:#fb7185}*{box-sizing:border-box}body{margin:0;font-family:Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif;background:radial-gradient(circle at top left,#1d4ed833,transparent 34rem),var(--bg);color:var(--text)}main{max-width:1180px;margin:0 auto;padding:32px 20px 64px}.hero{display:flex;justify-content:space-between;gap:24px;align-items:flex-start;margin-bottom:28px}.badge{display:inline-flex;gap:8px;align-items:center;border:1px solid #2a3a5e;background:#0f172a;padding:8px 12px;border-radius:999px;color:#bfdbfe;font-size:14px}h1{font-size:clamp(32px,5vw,58px);line-height:1;margin:16px 0 12px;letter-spacing:-.04em}.lead{color:var(--muted);font-size:18px;max-width:760px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px}.card{border:1px solid #253653;background:linear-gradient(180deg,#16213acc,#10172acc);border-radius:24px;padding:22px;box-shadow:0 20px 60px #0006}.card h2,.card h3{margin-top:0}.muted{color:var(--muted)}.pill{display:inline-block;border-radius:999px;padding:5px 10px;background:#1e293b;color:#bfdbfe;font-size:12px;margin:2px}.actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:14px}.btn,button{border:0;border-radius:14px;background:linear-gradient(135deg,#3b82f6,#06b6d4);color:white;padding:10px 14px;font-weight:700;cursor:pointer;text-decoration:none}.btn.secondary{background:#1f2a44;color:#cfe2ff;border:1px solid #33476d}input,textarea,select{width:100%;border:1px solid #314262;background:#0b1222;color:var(--text);border-radius:14px;padding:11px;margin:6px 0 12px}textarea{min-height:110px;font-family:ui-monospace,Menlo,monospace}.status-ok{color:var(--ok)}.status-failed{color:var(--bad)}table{width:100%;border-collapse:collapse}td,th{border-bottom:1px solid #263653;padding:10px;text-align:left;vertical-align:top}code{color:#bfdbfe}.section{margin-top:26px}.small{font-size:13px}.split{display:grid;grid-template-columns:1.2fr .8fr;gap:18px}@media(max-width:850px){.hero,.split{display:block}.card{margin-bottom:16px}}
"""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def load_tasks() -> dict[str, TaskDef]:
    payload = json.loads(REGISTRY_PATH.read_text(encoding='utf-8'))
    return {item['id']: TaskDef(**item) for item in payload.get('tasks', [])}


def load_optional_tasks() -> dict[str, TaskDef]:
    tasks: dict[str, TaskDef] = {}
    for path in [ROOT / 'automation' / 'tasks.sweb.json']:
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding='utf-8'))
        for item in payload.get('tasks', []):
            task = TaskDef(**item)
            tasks.setdefault(task.id, task)
    return tasks



def save_schedules() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {'schedules': [schedule.__dict__ for schedule in SCHEDULES.values()]}
    SCHEDULES_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


def load_schedules() -> dict[str, ScheduleDef]:
    if not SCHEDULES_PATH.exists():
        return {}
    payload = json.loads(SCHEDULES_PATH.read_text(encoding='utf-8'))
    return {item['id']: ScheduleDef(**item) for item in payload.get('schedules', [])}


def render_page(content: str) -> HTMLResponse:
    return HTMLResponse(f"""<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>SpaceWeb Control Plane</title><style>{STYLE}</style></head><body><main><div class="hero"><div><span class="badge">● Knative-ready FastAPI</span><h1>Панель управления инфраструктурой SpaceWeb</h1><p class="lead">Запускайте Python-скрипты из Git-репозитория вручную или по расписанию. UI построен для serverless-контейнера: порт берётся из переменной <code>PORT</code>, есть health-check и лёгкий in-process scheduler.</p></div><div class="card"><b>Команды деплоя</b><p class="small muted">Build: <code>python -m compileall app client automation</code></p><p class="small muted">Start: <code>uvicorn app.main:app --host 0.0.0.0 --port ${{PORT:-8080}}</code></p></div></div>{content}</main></body></html>""")


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def require_auth(credentials: HTTPBasicCredentials = Depends(SECURITY)) -> str:
    user_ok = secrets.compare_digest(credentials.username, CONTROL_PLANE_USER)
    password_ok = secrets.compare_digest(credentials.password, CONTROL_PLANE_PASSWORD)
    if not (user_ok and password_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid control plane credentials',
            headers={'WWW-Authenticate': 'Basic'},
        )
    return credentials.username



def service_map() -> dict[str, list[TaskDef]]:
    services: dict[str, list[TaskDef]] = {}
    for task in TASKS.values():
        services.setdefault(task.service, []).append(task)
    return services


async def execute_task(task_id: str, params: dict[str, Any], source: str) -> dict[str, Any]:
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail='Unknown task')
    script = (ROOT / task.script).resolve()
    if not script.is_file() or ROOT not in script.parents:
        raise HTTPException(status_code=400, detail='Task script is not allowed')
    started = utc_now()
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        str(script),
        '--params-json',
        json.dumps(params, ensure_ascii=False),
        cwd=str(ROOT),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    status = 'ok' if proc.returncode == 0 else 'failed'
    log = {
        'id': uuid.uuid4().hex[:12],
        'task_id': task_id,
        'task_title': task.title,
        'source': source,
        'status': status,
        'returncode': proc.returncode,
        'started_at': iso(started),
        'finished_at': iso(utc_now()),
        'stdout': stdout.decode(errors='replace')[-4000:],
        'stderr': stderr.decode(errors='replace')[-4000:],
    }
    RUN_LOGS.insert(0, log)
    del RUN_LOGS[MAX_LOGS:]
    return log


async def scheduler_loop() -> None:
    while True:
        now = utc_now()
        changed = False
        for schedule in list(SCHEDULES.values()):
            next_run = parse_dt(schedule.next_run_at)
            if schedule.enabled and (next_run is None or next_run <= now):
                try:
                    log = await execute_task(schedule.task_id, schedule.params, f'schedule:{schedule.id}')
                    schedule.last_status = log['status']
                except Exception as exc:  # noqa: BLE001 - scheduler must keep running
                    schedule.last_status = f'failed: {exc}'
                schedule.last_run_at = iso(now)
                schedule.next_run_at = iso(datetime.fromtimestamp(now.timestamp() + schedule.interval_minutes * 60, tz=timezone.utc))
                changed = True
        if changed:
            save_schedules()
        await asyncio.sleep(15)


@app.on_event('startup')
async def startup() -> None:
    global TASKS, SCHEDULES, SCHEDULER_TASK
    TASKS = load_tasks()
    TASKS.update({task_id: task for task_id, task in load_optional_tasks().items() if task_id not in TASKS})
    SCHEDULES = load_schedules()
    SCHEDULER_TASK = asyncio.create_task(scheduler_loop())


@app.on_event('shutdown')
async def shutdown() -> None:
    if SCHEDULER_TASK:
        SCHEDULER_TASK.cancel()


@app.get('/healthz')
def healthz() -> dict[str, str]:
    return {'status': 'ok'}


@app.get('/', response_class=HTMLResponse)
def index(_user: str = Depends(require_auth)) -> HTMLResponse:

    service_cards = ''.join(
        f"<div class='card'><h3>{esc(service)}</h3><p class='muted'>{len(tasks)} доступных действий</p>" +
        ''.join(f"<div><span class='pill'>{esc(t.id)}</span><b>{esc(t.title)}</b><p class='muted small'>{esc(t.description)}</p><div class='actions'><a class='btn secondary' href='/tasks/{esc(t.id)}'>Открыть</a></div></div>" for t in tasks) +
        '</div>'
        for service, tasks in service_map().items()
    )
    schedules = ''.join(
        f"<tr><td>{esc(s.title)}<br><span class='muted small'>{esc(s.task_id)}</span></td><td>{s.interval_minutes} мин</td><td>{esc(s.next_run_at or '—')}</td><td>{esc(s.last_status or '—')}</td></tr>"
        for s in SCHEDULES.values()
    ) or "<tr><td colspan='4' class='muted'>Расписаний пока нет</td></tr>"
    logs = ''.join(
        f"<tr><td>{esc(l['finished_at'])}<br><span class='muted small'>{esc(l['source'])}</span></td><td>{esc(l['task_title'])}</td><td class='status-{esc(l['status'])}'>{esc(l['status'])}</td><td><pre>{esc((l['stdout'] or l['stderr'])[:500])}</pre></td></tr>"
        for l in RUN_LOGS[:10]
    ) or "<tr><td colspan='4' class='muted'>Запусков пока нет</td></tr>"
    return render_page(f"""
    <div class="grid">{service_cards}</div>
    <div class="section split"><div class="card"><h2>Расписание</h2><table><tr><th>Задача</th><th>Интервал</th><th>Следующий запуск</th><th>Статус</th></tr>{schedules}</table></div><div class="card"><h2>Создать расписание</h2><form action="/schedules" method="post"><label>Действие</label><select name="task_id">{''.join(f'<option value="{esc(t.id)}">{esc(t.service)} · {esc(t.title)}</option>' for t in TASKS.values())}</select><label>Название</label><input name="title" placeholder="Например: ежедневная проверка"><label>Интервал, минут</label><input name="interval_minutes" type="number" min="1" value="60"><label>Параметры JSON</label><textarea name="params_json">{{}}</textarea><button>Запланировать</button></form></div></div>
    <div class="section card"><h2>Последние запуски</h2><table><tr><th>Время</th><th>Задача</th><th>Статус</th><th>Вывод</th></tr>{logs}</table></div>
    """)


@app.get('/tasks/{task_id}', response_class=HTMLResponse)
def task_page(task_id: str, _user: str = Depends(require_auth)) -> HTMLResponse:
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail='Unknown task')
    params = json.dumps(task.default_params, ensure_ascii=False, indent=2)
    return render_page(f"""<div class="card"><a class="btn secondary" href="/">← Назад</a><h2>{esc(task.title)}</h2><p class="muted">{esc(task.description)}</p><p><span class="pill">{esc(task.service)}</span><span class="pill">{esc(task.id)}</span><span class="pill">{esc(task.script)}</span></p><form action="/tasks/{esc(task.id)}/run" method="post"><label>Параметры JSON</label><textarea name="params_json">{esc(params)}</textarea><button>Запустить сейчас</button></form></div>""")


@app.post('/tasks/{task_id}/run')
async def run_task(task_id: str, params_json: str = Form('{}'), _user: str = Depends(require_auth)) -> RedirectResponse:

    params = json.loads(params_json or '{}')
    await execute_task(task_id, params, 'manual')
    return RedirectResponse('/', status_code=303)


@app.post('/schedules')
def create_schedule(task_id: str = Form(...), title: str = Form(''), interval_minutes: int = Form(60), params_json: str = Form('{}'), _user: str = Depends(require_auth)) -> RedirectResponse:

    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail='Unknown task')
    schedule = ScheduleDef(
        id=uuid.uuid4().hex[:12],
        task_id=task_id,
        title=title or TASKS[task_id].title,
        interval_minutes=max(1, interval_minutes),
        params=json.loads(params_json or '{}'),
        next_run_at=iso(utc_now()),
    )
    SCHEDULES[schedule.id] = schedule
    save_schedules()
    return RedirectResponse('/', status_code=303)
