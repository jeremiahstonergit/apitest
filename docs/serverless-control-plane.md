# Serverless control plane specification

## Цель

Добавить к репозиторию web-приложение для Knative Serving, которое позволяет запускать Python-скрипты управления инфраструктурой из Git-репозитория вручную и по расписанию.

## Выбранный стек

- **FastAPI** — подходит лучше Flask для этого проекта, потому что даёт OpenAPI из коробки, async lifecycle, простые health-check endpoints и хорошо запускается через `uvicorn` в Knative Serving.
- **In-process scheduler на `asyncio`** — минимальная зависимость для MVP. Для критичных production-задач в serverless-среде рекомендуется заменить/дополнить его внешним триггером: Knative Eventing, Kubernetes CronJob или managed scheduler, потому что инстанс Knative Serving может масштабироваться до нуля.
- **Python scripts registry** — список разрешённых действий хранится в `automation/tasks.registry.json`; UI не запускает произвольные shell-команды.

## Пользовательские сценарии

1. Открыть `/` и увидеть список услуг.
2. Выбрать услугу и действие.
3. Передать параметры в JSON и запустить действие вручную.
4. Создать расписание для выбранного действия с интервалом в минутах и параметрами.
5. Посмотреть последние запуски, статус и stdout/stderr.

## Архитектура

```text
Knative HTTP request
        │
        ▼
FastAPI app (`app/main.py`)
        │
        ├── UI `/`
        ├── Health `/healthz`
        ├── Manual task run `/tasks/{task_id}/run`
        └── asyncio scheduler loop
                │
                ▼
Allowed Python scripts from `automation/tasks.registry.json`
```

## Контракт задачи

Каждая задача регистрируется в `automation/tasks.registry.json`:

```json
{
  "id": "example.echo",
  "title": "Проверочная задача",
  "service": "system",
  "description": "...",
  "script": "automation/tasks/example_echo.py",
  "default_params": {"message": "hello"}
}
```

Скрипт вызывается так:

```bash
python automation/tasks/example_echo.py --params-json '{"message":"hello"}'
```

## Команды для serverless-платформы

Build command:

```bash
python -m compileall app client automation
```

Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
```

## Переменные окружения

| Имя | Значение по умолчанию | Описание |
| --- | --- | --- |
| `PORT` | `8080` | Порт HTTP-сервера, обычно задаётся платформой. |
| `SWEB_AUTOMATION_DATA_DIR` | `.runtime` | Каталог для `schedules.json`; в Knative ephemeral, для production нужен volume или внешний storage. |
| `SWEB_AUTOMATION_MAX_LOGS` | `50` | Максимум записей в памяти о последних запусках. |

## Аккаунт SpaceWeb и секреты

Приложение не подключается ни к какому аккаунту SpaceWeb по умолчанию. Включённая задача `example.echo` является локальной demo-задачей и не делает API-вызовов.

Реальные секреты доступа нельзя хранить в Git. Их нужно создать в secret manager serverless-платформы и пробросить в контейнер переменными окружения. Рекомендуемые имена для будущих automation-скриптов:

| Имя | Значение | Назначение |
| --- | --- | --- |
| `SWEB_API_LOGIN` | `<login>` | Логин SpaceWeb. Обычный режим: скрипт вызывает `getToken` с этим значением. |
| `SWEB_API_PASSWORD` | `<password>` | Пароль SpaceWeb. Обычный режим: скрипт вызывает `getToken` с этим значением. |
| `SWEB_API_TOKEN` | `<token>` | Опциональный временный Bearer token, только если вы получили его вне приложения. Это результат `getToken`, а не статичный токен из репозитория. |

В обычном сценарии `SWEB_API_TOKEN` не нужно придумывать или искать вручную: задайте `SWEB_API_LOGIN` и `SWEB_API_PASSWORD`, а automation-скрипт сам получает токен через `POST https://api.sweb.ru/notAuthorized/` с методом `getToken`. Затем этот токен передаётся как `Authorization: Bearer <token>` для защищённых вызовов.

## Ограничения MVP

- Расписания сохраняются локально в JSON-файл; при ephemeral filesystem они не являются долговечными.
- При нескольких репликах scheduler будет работать в каждой реплике. Для production нужен leader election или внешний планировщик.
- UI намеренно запускает только зарегистрированные скрипты внутри репозитория.
