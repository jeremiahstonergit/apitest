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

## Ограничения MVP

- Расписания сохраняются локально в JSON-файл; при ephemeral filesystem они не являются долговечными.
- При нескольких репликах scheduler будет работать в каждой реплике. Для production нужен leader election или внешний планировщик.
- UI намеренно запускает только зарегистрированные скрипты внутри репозитория.
