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

## SpaceWeb API account and secrets

The control plane does **not** connect to any SpaceWeb account by default. The included `example.echo` task is a local demo and does not call the SpaceWeb API.

Do not commit real credentials to this repository. Store secrets in the serverless platform secret manager and expose them to runtime as environment variables. Suggested names for automation scripts are:

| Name | Value | Purpose |
| --- | --- | --- |
| `SWEB_API_LOGIN` | `<login>` | SpaceWeb login. Normal mode: scripts call `getToken` with this value. |
| `SWEB_API_PASSWORD` | `<password>` | SpaceWeb password. Normal mode: scripts call `getToken` with this value. |
| `SWEB_API_TOKEN` | `<token>` | Optional temporary Bearer token only if you obtained it outside this app. This is the result of `getToken`, not a static token from the repository. |

In the normal flow you do **not** manually invent or look up `SWEB_API_TOKEN`: configure `SWEB_API_LOGIN` and `SWEB_API_PASSWORD`, then an automation script obtains the token by calling `POST https://api.sweb.ru/notAuthorized/` with method `getToken`. After that it sends `Authorization: Bearer <token>` for protected API calls.

## Runtime

Select **Python** or **FastAPI** as the serverless runtime and install dependencies from `requirements.txt` before running the start command.
