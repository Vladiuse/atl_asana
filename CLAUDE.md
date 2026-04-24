# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**atl_asana** is a Django 5 service that automates internal processes for an agency. It integrates with Asana API, sends notifications to Telegram, and processes webhooks. The app runs as a Docker Compose stack with separate web, Celery worker, Celery beat, and valentine-bot containers.

## Architecture

### Layered Design
Each Django app follows a consistent 4-layer architecture:

- **Models** (`models.py`) — ORM definitions
- **Repository** (`repository.py`) — Data access layer that wraps queries
- **Services** (`services.py`) — Business logic orchestration
- **Views** (`views.py`) — DRF endpoints

Some apps add:
- **Use Cases** (`use_cases.py`) — Higher-level orchestration or domain logic
- **Tasks** (`tasks.py`) — Celery async jobs
- **Webhook Actions** (`webhook_actions/`) — Event-driven handlers (asana app)
- **Management Commands** (`management/`) — Django CLI tools

### Core Apps

| App | Purpose |
|-----|---------|
| `asana` | Asana API integration, tasks, projects, webhooks |
| `offboarding` | Employee offboarding workflows |
| `comment_notifier` | Comment notification system |
| `creative_quality` | Creative asset quality control |
| `leave_events` | Vacation/time-off event handling |
| `message_sender` | Message dispatch (Telegram, etc.) |
| `valentine_day` | Valentine's Day Telegram bot |
| `vga_lands` | Landing pages |
| `fake_message` | Test message generation |
| `webhook_pinger` | Webhook monitoring |
| `common` | Shared utilities and base classes |

## Tech Stack

- **Framework**: Django 5 + DRF (Django REST Framework)
- **Task Queue**: Celery 5.5 + Redis 7 (worker + periodic beat)
- **Database**: PostgreSQL 15
- **HTTP Client**: httpx
- **External APIs**: Asana, Telegram Bot API, Google Sheets (gspread)
- **Type Checking**: mypy with django-stubs, strict mode
- **Linting**: ruff with max line length 119
- **Testing**: pytest + pytest-django (socket disabled by default)
- **Deployment**: Docker Compose + nginx

## Development Commands

### Setup
```bash
# Create .env from template
cp env-example .env

# Start all services (web, db, redis, celery, nginx, valentine-bot)
docker compose up -d

# Apply migrations
docker compose exec atl-asana-web python manage.py migrate

# Create superuser
docker compose exec atl-asana-web python manage.py createsuperuser
```

### Running Code Quality Tools
From the project root:

```bash
# Run tests (with socket disabled)
pytest

# Run a single test file
pytest app/asana/tests/test_models.py

# Run tests matching a pattern
pytest -k "test_webhook" -v

# Run with coverage
pytest --cov=app --cov-report=html

# Linting
ruff check app/

# Auto-fix linting issues
ruff check --fix app/

# Code formatting
ruff format app/

# Type checking
mypy

# Type checking a specific module
mypy app/asana/
```

### Django Management
Run from within the web container or with `python app/manage.py`:

```bash
# Migrations
python app/manage.py migrate
python app/manage.py makemigrations

# Development server
python app/manage.py runserver 0.0.0.0:8000

# Create fixtures / seed data
python app/manage.py dumpdata > fixtures.json
python app/manage.py loaddata fixtures.json

# Shell with Django context
python app/manage.py shell
```

## Testing Notes

- **Socket disabled**: `pytest_socket` disables network calls by default to prevent accidental external API calls
- **API client fixture**: Use `api_client` fixture from `conftest.py` for DRF tests
- **Django settings**: Uses `atl_asana.settings` (DJANGO_SETTINGS_MODULE)
- **Test discovery**: Matches `tests.py`, `test_*.py`, `*_tests.py`
- **Assertion on template variables**: FAIL_INVALID_TEMPLATE_VARS = True

## Configuration

### Ruff (Linting & Formatting)
- **Line length**: 119
- **Style**: Double quotes, 2-space indent
- **Ignores per-file**:
  - Migrations: all rules
  - `manage.py`: all rules
  - Views: `A002` (shadowing builtins)
  - Tests: `PT027`, `PLR2004`, `S101`, `SLF001`, `DTZ001`, `FBT001`
  - Scripts in `_temp/` and named `x.py`: all rules

### mypy (Type Checking)
- **Mode**: Strict (with Django exceptions)
- **Excludes**: `manage.py`, migrations, `_temp/`, `scripts/x.py`
- **Key settings**: Django plugin enabled, `ignore_missing_imports=true`, `no_implicit_optional=false`
- **Focus**: Models are strictly checked; other code is lenient for Django patterns

### Django Settings
- **Path**: `app/atl_asana/settings.py`
- **Celery config**: `app/atl_asana/celery.py`
- **Celery signals**: `app/atl_asana/celery_signals.py`

## Key Files & Patterns

### Environment & Secrets
- `.env` — Local environment variables (database, Redis, Telegram token, etc.)
- `env-example` — Template for required variables
- `service_account.json` — Google service account (for gspread integration)

### Celery Tasks
Add tasks in each app's `tasks.py`:
```python
from celery import shared_task

@shared_task
def my_async_task(arg):
    pass
```

Celery beat scheduler picks up Django-Celery-Beat models. Register periodic tasks in the Django admin.

### Webhook Actions (Asana)
The `asana/webhook_actions/` module processes incoming Asana webhooks. Each action handler is a callable that reacts to Asana events.

### Docker Compose Services
- **atl-asana-web** — Main Django/Gunicorn service
- **celery_worker** — Async task runner
- **celery_beat** — Periodic task scheduler
- **valentine-bot** — Standalone Telegram bot (runs `valentine_bot.py`)
- **nginx** — Reverse proxy + static/media serving
- **db** — PostgreSQL 15
- **redis** — Cache + message broker

Port mapping: nginx on `${NGINX_PORT}`, redis on `26379`.

## Common Workflows

### Adding a New Feature
1. Create models in the app's `models.py`
2. Create a repository layer if multiple queries are needed
3. Implement business logic in `services.py` or `use_cases.py`
4. Add views (DRF viewsets) in `views.py`
5. Register URLs in the app's `urls.py`
6. Add Celery tasks if async work is needed
7. Write tests in `tests/`
8. Run `ruff check --fix` and `mypy` before commit

### Async Operations
Use Celery for long-running tasks:
- Define task in `tasks.py`
- Call with `.delay()` or `.apply_async()`
- Monitor via Celery worker logs or django-celery-results

### Database Queries
Use the repository pattern:
```python
# In models.py or repositories:
objects = Manager()

# In services.py:
user = repository.get_user_by_email(email)
```

Avoid ORM calls in views — move them to services.

## Logging

Logs are typically written to `app/logs/` directory (see docker-compose for volume mounts). Check `app/general.log` for application events.

## Known Issues & Notes

- Tests have socket disabled to prevent unintended API calls
- Django-stubs and mypy.ini configured for Django models flexibility
- Migration files are excluded from linting to reduce noise
- The valentine-bot container restarts automatically if it fails
