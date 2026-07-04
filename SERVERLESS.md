# Serverless deployment settings

Use these values when connecting this repository to a Python/FastAPI serverless runtime such as Knative Serving.

## Build command

```bash
python -m compileall app client automation
```

## Start command

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

If the platform injects its own port as `PORT`, use this variant instead:

```bash
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
```

## Environment variables

Required variables: none.

Optional variables:

| Name | Value | Purpose |
| --- | --- | --- |
| `PORT` | `8080` | HTTP port. Usually set by Knative/serverless platform automatically. |
| `SWEB_AUTOMATION_DATA_DIR` | `.runtime` | Directory for the local `schedules.json` file. Use persistent storage for production schedules. |
| `SWEB_AUTOMATION_MAX_LOGS` | `50` | Maximum number of recent run logs kept in memory. |

## Runtime

Select **Python** or **FastAPI** as the serverless runtime and install dependencies from `requirements.txt` before running the start command.
