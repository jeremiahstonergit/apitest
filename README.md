# sweb-api-llm-spec

LLM-first слой для SpaceWeb API: projection/transport OpenAPI-спеки, валидированные примеры, auth-артефакты, адаптеры и MCP-инструменты для coding-агентов.

## Что это

`sweb-api-llm-spec` преобразует документацию SpaceWeb API в машиночитаемый и агентно-ориентированный набор артефактов для разработки.

Проект разделяет два слоя:

- **LLM projection spec** — семантический слой для понимания API моделью
- **Transport spec** — исполнимый слой для реальных JSON-RPC вызовов

Репозиторий дополнительно содержит:

- валидированные request/response examples
- описание авторизации в human- и machine-readable формате
- Python и TypeScript transport adapters
- MCP-сервер для поиска операций, схем, примеров и сборки transport-вызовов
- нативные инструкции для Codex, Copilot, Cursor, Claude Code и Windsurf
- pipeline обновления репозитория при изменении или добавлении методов API

## Структура

- `spec/openapi.llm-projection.yaml` — LLM-friendly planning layer
- `spec/openapi.transport.yaml` — executable transport layer
- `examples/examples.jsonl` — валидированные примеры
- `auth/` — auth flow и machine-readable auth metadata
- `client/python/` — Python adapter + generated operations map
- `client/ts/` — TypeScript adapter + generated operations map
- `mcp/` — MCP server
- `notes/raw/schema/` — raw upstream OpenRPC snapshots
- `sources/manifest.json` — manifest текущего snapshot'а и сгенерированных артефактов
- `notes/update-summary.latest.{json,md}` — результат последнего пересчета
- `scripts/update_repo.py` — единая точка обновления репозитория

## Поддерживаемые инструменты

- OpenAI Codex
- GitHub Copilot coding agent
- Cursor
- Claude Code
- Windsurf

## Команды

Полная пересборка из текущих raw-источников:

```bash
python3 scripts/update_repo.py --rebuild-only
```

Импорт нового snapshot-каталога и пересборка:

```bash
python3 scripts/update_repo.py --source-dir /path/to/snapshot
```

Импорт нового snapshot-архива и пересборка:

```bash
python3 scripts/update_repo.py --source-archive /path/to/snapshot.tar.gz
```

Частичная сборка для отладки:

```bash
python3 scripts/update_repo.py --rebuild-only --limit 50
```

## Как обновляется репозиторий при изменении API

Репозиторий не предполагает ручное редактирование итоговых spec-файлов как основной процесс.

Правильный поток такой:

1. Получить новый raw snapshot документации/API-метаданных
2. Импортировать snapshot через `scripts/update_repo.py`
3. Автоматически пересобрать:
   - projection spec
   - transport spec
   - examples
   - operations maps
   - update summary
   - manifest
4. Прогнать validation
5. Проверить diff в PR
6. Выпустить release

Подробно процесс описан в `docs/update-process.md` и `docs/release-process.md`.

## Статус

Текущий статус: **production-usable for agentic coding under controlled rollout**.

## Версионирование

Используется семантическое версионирование:

- `MAJOR` — breaking changes в transport/auth/contract
- `MINOR` — новые операции, новые namespaces, расширение покрытия
- `PATCH` — фиксы схем, examples, docs, CI, tooling

## Agent-native files

- Codex/OpenAI: `AGENTS.md`
- Claude Code: `CLAUDE.md`, `.claude/README.md`
- Copilot: `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md`
- Cursor: `.cursor/rules/*.mdc`
- Windsurf: `.windsurf/rules/*`
- MCP lookup server: `mcp/server.py`

## Serverless web control plane

В репозиторий добавлен MVP web-интерфейса для запуска Python-скриптов управления инфраструктурой в Knative Serving.

- приложение: `app/main.py`
- registry разрешённых действий: `automation/tasks.registry.json`
- пример безопасной задачи: `automation/tasks/example_echo.py`
- спецификация и ограничения: `docs/serverless-control-plane.md`

Команда сборки для serverless-платформы:

```bash
python -m compileall app client automation
```

Команда запуска:

```bash
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
```

Рекомендуемые переменные окружения:

- `PORT=8080`
- `SWEB_AUTOMATION_DATA_DIR=.runtime`
- `SWEB_AUTOMATION_MAX_LOGS=50`
