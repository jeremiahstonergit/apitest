"""Application package for the SpaceWeb control plane."""


import os


def _merge_optional_task_catalogs() -> None:
    if os.getenv("SWEB_SKIP_TASK_CATALOG_MERGE") == "1":
        return

    try:
        from scripts.merge_task_catalogs import main as merge_task_catalogs
        merge_task_catalogs()
    except Exception:
        # In serverless/runtime environments the app filesystem can be read-only.
        # Optional task catalog merge must not prevent the API from starting.
        return


_merge_optional_task_catalogs()

