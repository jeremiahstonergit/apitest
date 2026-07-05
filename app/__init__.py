"""Application package for the SpaceWeb control plane."""
"""Application package bootstrap."""

from __future__ import annotations

import os


def _merge_optional_task_catalogs() -> None:
    if os.getenv('SWEB_SKIP_TASK_CATALOG_MERGE') == '1':
        return
    try:
        from scripts.merge_task_catalogs import main as merge_task_catalogs
    except Exception:
        return
    merge_task_catalogs()


_merge_optional_task_catalogs()
