"""Runtime state, persistence, and task execution helpers."""

from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / 'automation' / 'tasks.registry.json'
DATA_DIR = Path(os.getenv('SWEB_AUTOMATION_DATA_DIR', ROOT / '.runtime'))
SCHEDULES_PATH = DATA_DIR / 'schedules.json'
MAX_LOGS = int(os.getenv('SWEB_AUTOMATION_MAX_LOGS', '50'))


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


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def parse_params(value: str) -> dict[str, Any]:
    params = json.loads(value or '{}')
    if not isinstance(params, dict):
        raise HTTPException(status_code=400, detail='params_json must be an object')
    return params


def format_params(params: dict[str, Any]) -> str:
    return json.dumps(params, ensure_ascii=False, indent=2)


def new_id() -> str:
    return uuid.uuid4().hex[:12]


def load_tasks() -> dict[str, TaskDef]:
    payload = json.loads(REGISTRY_PATH.read_text(encoding='utf-8'))
    return {item['id']: TaskDef(**item) for item in payload.get('tasks', [])}


def save_schedules(schedules: dict[str, ScheduleDef]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {'schedules': [schedule.__dict__ for schedule in schedules.values()]}
    SCHEDULES_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


def load_schedules() -> dict[str, ScheduleDef]:
    if not SCHEDULES_PATH.exists():
        return {}
    payload = json.loads(SCHEDULES_PATH.read_text(encoding='utf-8'))
    return {item['id']: ScheduleDef(**item) for item in payload.get('schedules', [])}


async def execute_task(task: TaskDef, params: dict[str, Any], source: str) -> dict[str, Any]:
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
    return {
        'id': new_id(),
        'task_id': task.id,
        'task_title': task.title,
        'source': source,
        'status': status,
        'returncode': proc.returncode,
        'started_at': iso(started),
        'finished_at': iso(utc_now()),
        'stdout': stdout.decode(errors='replace')[-4000:],
        'stderr': stderr.decode(errors='replace')[-4000:],
    }
