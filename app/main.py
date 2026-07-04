"""FastAPI control plane for SpaceWeb infrastructure automation on Knative Serving."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from app.runtime import MAX_LOGS, ScheduleDef, TaskDef, execute_task as run_registered_task, format_params, iso, load_schedules, load_tasks, new_id, parse_dt, parse_params, save_schedules, utc_now
from app.ui import esc, render_page


app = FastAPI(
    title='SpaceWeb Infrastructure Control Plane',
    description='Web UI and lightweight scheduler for repository-managed Python automation scripts.',
    version='0.1.0',
)


TASKS: dict[str, TaskDef] = {}
SCHEDULES: dict[str, ScheduleDef] = {}
RUN_LOGS: list[dict[str, Any]] = []
SCHEDULER_TASK: asyncio.Task | None = None


def service_map() -> dict[str, list[TaskDef]]:
    services: dict[str, list[TaskDef]] = {}
    for task in TASKS.values():
        services.setdefault(task.service, []).append(task)
    return services


async def scheduler_loop() -> None:
    while True:
        now = utc_now()
        changed = False
        for schedule in list(SCHEDULES.values()):
            next_run = parse_dt(schedule.next_run_at)
            if schedule.enabled and (next_run is None or next_run <= now):
                try:
                    task = TASKS.get(schedule.task_id)
                    if not task:
                        raise HTTPException(status_code=404, detail='Unknown task')
                    log = await run_registered_task(task, schedule.params, f'schedule:{schedule.id}')
                    schedule.last_status = log['status']
                except Exception as exc:  # noqa: BLE001 - scheduler must keep running
                    schedule.last_status = f'failed: {exc}'
                schedule.last_run_at = iso(now)
                schedule.next_run_at = iso(datetime.fromtimestamp(now.timestamp() + schedule.interval_minutes * 60, tz=timezone.utc))
                changed = True
        if changed:
            save_schedules(SCHEDULES)
        await asyncio.sleep(15)


@app.on_event('startup')
async def startup() -> None:
    global TASKS, SCHEDULES, SCHEDULER_TASK
    TASKS = load_tasks()
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
def index() -> HTMLResponse:
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
def task_page(task_id: str) -> HTMLResponse:
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail='Unknown task')
    params = format_params(task.default_params)
    return render_page(f"""<div class="card"><a class="btn secondary" href="/">← Назад</a><h2>{esc(task.title)}</h2><p class="muted">{esc(task.description)}</p><p><span class="pill">{esc(task.service)}</span><span class="pill">{esc(task.id)}</span><span class="pill">{esc(task.script)}</span></p><form action="/tasks/{esc(task.id)}/run" method="post"><label>Параметры JSON</label><textarea name="params_json">{esc(params)}</textarea><button>Запустить сейчас</button></form></div>""")


@app.post('/tasks/{task_id}/run')
async def run_task(task_id: str, params_json: str = Form('{}')) -> RedirectResponse:
    params = parse_params(params_json)
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail='Unknown task')
    log = await run_registered_task(task, params, 'manual')
    RUN_LOGS.insert(0, log)
    del RUN_LOGS[MAX_LOGS:]
    return RedirectResponse('/', status_code=303)


@app.post('/schedules')
def create_schedule(task_id: str = Form(...), title: str = Form(''), interval_minutes: int = Form(60), params_json: str = Form('{}')) -> RedirectResponse:
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail='Unknown task')
    schedule = ScheduleDef(
        id=new_id(),
        task_id=task_id,
        title=title or TASKS[task_id].title,
        interval_minutes=max(1, interval_minutes),
        params=parse_params(params_json),
        next_run_at=iso(utc_now()),
    )
    SCHEDULES[schedule.id] = schedule
    save_schedules(SCHEDULES)
    return RedirectResponse('/', status_code=303)
