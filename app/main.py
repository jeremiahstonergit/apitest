"""FastAPI control plane for SpaceWeb infrastructure automation on Knative Serving."""

from __future__ import annotations

import asyncio
import base64
import html
import json
import os
import secrets
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse, RedirectResponse

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / 'automation' / 'tasks.registry.json'
DATA_DIR = Path(os.getenv('SWEB_AUTOMATION_DATA_DIR', ROOT / '.runtime'))
SCHEDULES_PATH = DATA_DIR / 'schedules.json'
MAX_LOGS = int(os.getenv('SWEB_AUTOMATION_MAX_LOGS', '50'))
CONTROL_PLANE_USER = os.getenv('CONTROL_PLANE_USER', 'shashkin')
CONTROL_PLANE_PASSWORD = os.getenv('CONTROL_PLANE_PASSWORD', 'dumbilla')
CONTROL_PLANE_REVISION = os.getenv('CONTROL_PLANE_REVISION', 'vps-auth-2026-07-06')

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
SERVICE_INVENTORY: dict[str, list[dict[str, Any]]] = {}
SECURITY = HTTPBasic()


STYLE = """
:root{color-scheme:dark;--bg:#0b1020;--panel:#11182c;--muted:#8fa3c7;--text:#edf4ff;--brand:#60a5fa;--ok:#34d399;--warn:#fbbf24;--bad:#fb7185}*{box-sizing:border-box}body{margin:0;font-family:Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif;background:radial-gradient(circle at top left,#1d4ed833,transparent 34rem),var(--bg);color:var(--text)}main{max-width:1180px;margin:0 auto;padding:32px 20px 64px}.hero{display:flex;justify-content:space-between;gap:24px;align-items:flex-start;margin-bottom:28px}.badge{display:inline-flex;gap:8px;align-items:center;border:1px solid #2a3a5e;background:#0f172a;padding:8px 12px;border-radius:999px;color:#bfdbfe;font-size:14px}h1{font-size:clamp(32px,5vw,58px);line-height:1;margin:16px 0 12px;letter-spacing:-.04em}.lead{color:var(--muted);font-size:18px;max-width:760px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px}.card{border:1px solid #253653;background:linear-gradient(180deg,#16213acc,#10172acc);border-radius:24px;padding:22px;box-shadow:0 20px 60px #0006}.card h2,.card h3{margin-top:0}.muted{color:var(--muted)}.pill{display:inline-block;border-radius:999px;padding:5px 10px;background:#1e293b;color:#bfdbfe;font-size:12px;margin:2px}.actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:14px}.btn,button{border:0;border-radius:14px;background:linear-gradient(135deg,#3b82f6,#06b6d4);color:white;padding:10px 14px;font-weight:700;cursor:pointer;text-decoration:none}.btn.secondary{background:#1f2a44;color:#cfe2ff;border:1px solid #33476d}input,textarea,select{width:100%;border:1px solid #314262;background:#0b1222;color:var(--text);border-radius:14px;padding:11px;margin:6px 0 12px}textarea{min-height:110px;font-family:ui-monospace,Menlo,monospace}.status-ok{color:var(--ok)}.status-failed{color:var(--bad)}table{width:100%;border-collapse:collapse}td,th{border-bottom:1px solid #263653;padding:10px;text-align:left;vertical-align:top}code{color:#bfdbfe}.section{margin-top:26px}.small{font-size:13px}.split{display:grid;grid-template-columns:1.2fr .8fr;gap:18px}.category-head{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}.task-list{display:grid;gap:12px;margin-top:10px}.task-row{border:1px solid #263653;background:#0b122288;border-radius:18px;padding:14px}.task-row h4{margin:0 0 6px}.task-group-title{margin:18px 0 8px;color:#bfdbfe}.kv{display:grid;grid-template-columns:minmax(150px,.35fr) 1fr;gap:8px;border-bottom:1px solid #263653;padding:7px 0}.kv b{color:#bfdbfe}.json-list{margin:6px 0 0 18px}.empty-state{border:1px dashed #33476d;border-radius:16px;padding:14px;color:var(--muted)}@media(max-width:850px){.hero,.split{display:block}.card{margin-bottom:16px}}
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
    return HTMLResponse(f"""<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>SpaceWeb Control Plane</title><style>{STYLE}</style></head><body><main><div class="hero"><div><span class="badge">● Knative-ready FastAPI · {esc(CONTROL_PLANE_REVISION)}</span><h1>Панель управления инфраструктурой SpaceWeb</h1><p class="lead">Запускайте Python-скрипты из Git-репозитория вручную или по расписанию. UI построен для serverless-контейнера: порт берётся из переменной <code>PORT</code>, есть health-check и лёгкий in-process scheduler.</p></div><div class="card"><b>Команды деплоя</b><p class="small muted">Build: <code>python -m compileall app client automation</code></p><p class="small muted">Start: <code>uvicorn app.main:app --host 0.0.0.0 --port ${{PORT:-8080}}</code></p><p class="small muted">Revision: <code>{esc(CONTROL_PLANE_REVISION)}</code></p></div></div>{content}</main></body></html>""")


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


def load_all_tasks() -> dict[str, TaskDef]:
    tasks = load_tasks()
    tasks.update({task_id: task for task_id, task in load_optional_tasks().items() if task_id not in tasks})
    return tasks


def ensure_tasks_loaded() -> None:
    if not TASKS:
        TASKS.update(load_all_tasks())


def basic_auth_is_valid(header: str | None) -> bool:
    if not header or not header.startswith('Basic '):
        return False
    try:
        decoded = base64.b64decode(header.removeprefix('Basic ').strip()).decode('utf-8')
    except Exception:  # noqa: BLE001 - malformed auth header should simply fail auth
        return False
    username, separator, password = decoded.partition(':')
    if not separator:
        return False
    return (
        secrets.compare_digest(username, CONTROL_PLANE_USER)
        and secrets.compare_digest(password, CONTROL_PLANE_PASSWORD)
    )


@app.middleware('http')
async def enforce_basic_auth(request: Request, call_next):  # type: ignore[no-untyped-def]
    if request.url.path in {'/healthz', '/versionz'}:
        return await call_next(request)
    if not basic_auth_is_valid(request.headers.get('authorization')):
        return HTMLResponse(
            'Authentication required',
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={'WWW-Authenticate': 'Basic'},
        )
    return await call_next(request)


def service_map() -> dict[str, list[TaskDef]]:
    services: dict[str, list[TaskDef]] = {}
    for task in TASKS.values():
        services.setdefault(task.service, []).append(task)
    return services


def operation_id(task: TaskDef) -> str:
    value = task.default_params.get('operation_id')
    return value if isinstance(value, str) else ''


def is_common_task(task: TaskDef) -> bool:
    op_id = operation_id(task)
    method = op_id.rsplit('_', 1)[-1] if '_' in op_id else op_id
    return method in {'index', 'getList', 'getAllIpList', 'plans', 'checks', 'getAvailableConfig', 'getFirstOrderInfo', 'getOrderInfo'}


def render_task_rows(tasks: list[TaskDef]) -> str:
    if not tasks:
        return '<div class="empty-state">Нет действий в этой группе</div>'
    return '<div class="task-list">' + ''.join(
        f"<div class='task-row'><h4>{esc(task.title)}</h4><p class='muted small'>{esc(task.description)}</p>"
        f"<p><span class='pill'>{esc(task.id)}</span><span class='pill'>{esc(operation_id(task) or 'local')}</span></p>"
        f"<div class='actions'><a class='btn secondary' href='/tasks/{esc(task.id)}'>Открыть</a></div></div>"
        for task in sorted(tasks, key=lambda item: item.title.lower())
    ) + '</div>'


def render_json_value(value: Any) -> str:
    if isinstance(value, dict):
        if not value:
            return '<span class="muted">{}</span>'
        return '<div>' + ''.join(
            f"<div class='kv'><b>{esc(key)}</b><span>{render_json_value(item)}</span></div>"
            for key, item in value.items()
        ) + '</div>'
    if isinstance(value, list):
        if not value:
            return '<span class="muted">пустой список</span>'
        preview = value[:8]
        suffix = f"<li class='muted'>… ещё {len(value) - len(preview)}</li>" if len(value) > len(preview) else ''
        return '<ol class="json-list">' + ''.join(f'<li>{render_json_value(item)}</li>' for item in preview) + suffix + '</ol>'
    if value is None:
        return '<span class="muted">null</span>'
    if isinstance(value, bool):
        return '<span class="status-ok">да</span>' if value else '<span class="status-failed">нет</span>'
    return esc(value)


def render_human_output(stdout: str, stderr: str) -> str:
    text = stdout or stderr
    if not text:
        return '<span class="muted">Нет вывода</span>'
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return f'<pre>{esc(text[:900])}</pre>'

    if isinstance(payload, dict) and 'result' in payload:
        return '<b>Результат API</b>' + render_json_value(payload.get('result'))
    if isinstance(payload, dict) and 'error' in payload:
        return '<b class="status-failed">Ошибка API</b>' + render_json_value(payload.get('error'))
    return render_json_value(payload)


def extract_items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        preferred_keys = ('items', 'list', 'data', 'vps', 'servers', 'services', 'result')
        for key in preferred_keys:
            items = extract_items(value.get(key))
            if items:
                return items
        for item in value.values():
            items = extract_items(item)
            if items:
                return items
    return []


def service_item_id(item: dict[str, Any]) -> str:
    for key in ('billingId', 'billing_id', 'id', 'serverId', 'serviceId'):
        value = item.get(key)
        if value not in (None, ''):
            return str(value)
    return ''


def service_item_title(item: dict[str, Any]) -> str:
    for key in ('alias', 'name', 'title', 'hostname', 'domain', 'ip', 'mainIp'):
        value = item.get(key)
        if value not in (None, ''):
            return str(value)
    item_id = service_item_id(item)
    return f'VPS {item_id}' if item_id else 'VPS без идентификатора'


def operation_params_for_item(task: TaskDef, item: dict[str, Any]) -> dict[str, Any]:
    params = dict(task.default_params.get('params') or {})
    item_id = service_item_id(item)
    if item_id:
        params.setdefault('billingId', item_id)
    return {'operation_id': operation_id(task), 'params': params}


def action_requires_extra_params(task: TaskDef, params: dict[str, Any]) -> bool:
    op_id = operation_id(task)
    return op_id in {'vps_rename', 'vps_create', 'vps_createFirst', 'vps_reinstallOs', 'vps_changePlan'} or not params.get('billingId')


def render_service_action(task: TaskDef, item: dict[str, Any]) -> str:
    payload = operation_params_for_item(task, item)
    params_json = json.dumps(payload, ensure_ascii=False)
    if action_requires_extra_params(task, payload['params']):
        query = '&'.join(f'{esc(key)}={esc(value)}' for key, value in payload['params'].items())
        href = f'/tasks/{esc(task.id)}' + (f'?{query}' if query else '')
        return f"<a class='btn secondary' href='{href}'>{esc(task.title)}</a>"
    return (
        f"<form action='/tasks/{esc(task.id)}/run' method='post' style='display:inline'>"
        f"<input type='hidden' name='params_json' value='{esc(params_json)}'>"
        f"<button type='submit'>{esc(task.title)}</button></form>"
    )


def render_vps_inventory(vps_tasks: list[TaskDef]) -> str:
    items = SERVICE_INVENTORY.get('vps', [])
    refresh_form = "<form action='/inventory/vps/refresh' method='post'><button type='submit'>Обновить список VPS</button></form>"
    if not items:
        return f"<div class='empty-state'>Список VPS ещё не загружен. Нажмите обновление или выполните общее действие «Список VPS».</div><div class='actions'>{refresh_form}</div>"
    rows = []
    for item in items:
        item_id = service_item_id(item)
        actions = ''.join(render_service_action(task, item) for task in vps_tasks)
        rows.append(
            f"<div class='task-row'><h4>{esc(service_item_title(item))}</h4>"
            f"<p><span class='pill'>billingId: {esc(item_id or '—')}</span></p>"
            f"<details><summary class='muted'>Параметры услуги</summary>{render_json_value(item)}</details>"
            f"<div class='actions'>{actions}</div></div>"
        )
    return f"<div class='actions'>{refresh_form}</div><div class='task-list'>{''.join(rows)}</div>"


async def refresh_inventory(service: str) -> None:
    ensure_tasks_loaded()
    if service != 'vps' or 'vps.index' not in TASKS:
        return
    log = await execute_task('vps.index', {'operation_id': 'vps_index', 'params': {}}, f'inventory:{service}')
    if log['status'] != 'ok':
        return
    try:
        payload = json.loads(log.get('stdout') or '{}')
    except json.JSONDecodeError:
        return
    SERVICE_INVENTORY[service] = extract_items(payload.get('result', payload))


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
    TASKS = load_all_tasks()
    SCHEDULES = load_schedules()
    asyncio.create_task(refresh_inventory('vps'))
    SCHEDULER_TASK = asyncio.create_task(scheduler_loop())


@app.on_event('shutdown')
async def shutdown() -> None:
    if SCHEDULER_TASK:
        SCHEDULER_TASK.cancel()


@app.get('/healthz')
def healthz() -> dict[str, str]:
    return {'status': 'ok'}



@app.get('/versionz')
def versionz() -> dict[str, Any]:
    tasks = load_all_tasks()
    return {
        'revision': CONTROL_PLANE_REVISION,
        'tasks_total': len(tasks),
        'vps_tasks': sum(1 for task in tasks.values() if task.service == 'vps'),
        'vh_tasks': sum(1 for task in tasks.values() if task.service == 'vh'),
        'auth_enabled': True,
    }


@app.post('/inventory/vps/refresh')
async def refresh_vps_inventory(_user: str = Depends(require_auth)) -> RedirectResponse:
    await refresh_inventory('vps')
    return RedirectResponse('/', status_code=303)


@app.get('/', response_class=HTMLResponse)
def index(_user: str = Depends(require_auth)) -> HTMLResponse:
    ensure_tasks_loaded()
    all_tasks = list(TASKS.values())
    vps_common_tasks = [task for task in all_tasks if task.service == 'vps' and is_common_task(task)]
    vps_action_tasks = [task for task in all_tasks if task.service == 'vps' and not is_common_task(task)]
    common_tasks = [task for task in all_tasks if task.service != 'vps'] + vps_common_tasks
    schedules = ''.join(
        f"<tr><td>{esc(s.title)}<br><span class='muted small'>{esc(s.task_id)}</span></td><td>{s.interval_minutes} мин</td><td>{esc(s.next_run_at or '—')}</td><td>{esc(s.last_status or '—')}</td></tr>"
        for s in SCHEDULES.values()
    ) or "<tr><td colspan='4' class='muted'>Расписаний пока нет</td></tr>"
    logs = ''.join(
        f"<tr><td>{esc(l['finished_at'])}<br><span class='muted small'>{esc(l['source'])}</span></td><td>{esc(l['task_title'])}</td><td class='status-{esc(l['status'])}'>{esc(l['status'])}</td><td>{render_human_output(l.get('stdout', ''), l.get('stderr', ''))}</td></tr>"
        for l in RUN_LOGS[:10]
    ) or "<tr><td colspan='4' class='muted'>Запусков пока нет</td></tr>"
    return render_page(f"""
    <div class="section card"><h2>Выбор услуги</h2><p class="muted">Сначала выберите конкретную услугу, затем команду. Для VPS в запрос автоматически подставляется <code>billingId</code> выбранной услуги.</p><div class="actions"><a class="btn secondary" href="#vps-services">VPS услуги · {len(SERVICE_INVENTORY.get('vps', []))}</a><a class="btn secondary" href="#common-tasks">Общие задачи · {len(common_tasks)}</a></div></div>
    <section class="section card" id="vps-services"><div class="category-head"><div><h2>VPS услуги</h2><p class="muted">Выберите VPS из списка и запустите команду — параметры услуги попадут в API-запрос автоматически.</p></div><span class="pill">{len(vps_action_tasks)} команд</span></div>{render_vps_inventory(vps_action_tasks)}</section>
    <section class="section card" id="common-tasks"><h2>Общие задачи</h2><p class="muted">Задачи категории и справочные API-вызовы, которые не привязаны к конкретной услуге.</p>{render_task_rows(common_tasks)}</section>
    <div class="section split"><div class="card"><h2>Расписание</h2><table><tr><th>Задача</th><th>Интервал</th><th>Следующий запуск</th><th>Статус</th></tr>{schedules}</table></div><div class="card"><h2>Создать расписание</h2><form action="/schedules" method="post"><label>Действие</label><select name="task_id">{''.join(f'<option value="{esc(t.id)}">{esc(t.service)} · {esc(t.title)}</option>' for t in TASKS.values())}</select><label>Название</label><input name="title" placeholder="Например: ежедневная проверка"><label>Интервал, минут</label><input name="interval_minutes" type="number" min="1" value="60"><label>Параметры JSON</label><textarea name="params_json">{{}}</textarea><button>Запланировать</button></form></div></div>
    <div class="section card"><h2>Последние запуски</h2><table><tr><th>Время</th><th>Задача</th><th>Статус</th><th>Читаемый результат</th></tr>{logs}</table></div>
    """)


@app.get('/tasks/{task_id}', response_class=HTMLResponse)
def task_page(task_id: str, request: Request, _user: str = Depends(require_auth)) -> HTMLResponse:
    ensure_tasks_loaded()
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail='Unknown task')
    prefilled = json.loads(json.dumps(task.default_params, ensure_ascii=False))
    if request.query_params:
        task_params = dict(prefilled.get('params') or {})
        for key, value in request.query_params.items():
            task_params[key] = value
        prefilled['params'] = task_params
    params = json.dumps(prefilled, ensure_ascii=False, indent=2)
    return render_page(f"""<div class="card"><a class="btn secondary" href="/">← Назад</a><h2>{esc(task.title)}</h2><p class="muted">{esc(task.description)}</p><p><span class="pill">{esc(task.service)}</span><span class="pill">{esc(task.id)}</span><span class="pill">{esc(task.script)}</span></p><form action="/tasks/{esc(task.id)}/run" method="post"><label>Параметры JSON</label><textarea name="params_json">{esc(params)}</textarea><button>Запустить сейчас</button></form></div>""")


@app.post('/tasks/{task_id}/run')
async def run_task(task_id: str, params_json: str = Form('{}'), _user: str = Depends(require_auth)) -> RedirectResponse:
    ensure_tasks_loaded()
    params = json.loads(params_json or '{}')
    await execute_task(task_id, params, 'manual')
    return RedirectResponse('/', status_code=303)


@app.post('/schedules')
def create_schedule(task_id: str = Form(...), title: str = Form(''), interval_minutes: int = Form(60), params_json: str = Form('{}'), _user: str = Depends(require_auth)) -> RedirectResponse:
    ensure_tasks_loaded()
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
