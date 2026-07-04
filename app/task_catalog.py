"""Task catalog loading helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, TypeVar

T = TypeVar('T')


def load_task_items(base_registry: Path) -> list[dict]:
    """Load base registry plus optional SpaceWeb catalog next to it."""
    optional_catalogs = [base_registry.with_name('tasks.sweb.json')]
    items: list[dict] = []
    seen: set[str] = set()
    for path in [base_registry, *optional_catalogs]:
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding='utf-8'))
        for item in payload.get('tasks', []):
            task_id = item.get('id')
            if not isinstance(task_id, str) or task_id in seen:
                continue
            seen.add(task_id)
            items.append(item)
    return items


def load_tasks(base_registry: Path, factory: Callable[..., T]) -> dict[str, T]:
    return {item['id']: factory(**item) for item in load_task_items(base_registry)}
