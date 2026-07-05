#!/usr/bin/env python3
"""Merge optional task catalogs into automation/tasks.registry.json for deployment."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'automation' / 'tasks.registry.json'
OPTIONAL = [ROOT / 'automation' / 'tasks.sweb.json']


def main() -> None:
    tasks = []
    seen = set()
    for path in [BASE, *OPTIONAL]:
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding='utf-8'))
        for task in payload.get('tasks', []):
            task_id = task.get('id')
            if task_id in seen:
                continue
            seen.add(task_id)
            tasks.append(task)

    merged = json.dumps({'tasks': tasks}, ensure_ascii=False, indent=2) + '\n'
    if BASE.exists() and BASE.read_text(encoding='utf-8') == merged:
        return
    BASE.write_text(merged, encoding='utf-8')


if __name__ == '__main__':
    main()
