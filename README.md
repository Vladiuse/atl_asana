# atl_asana

Django-сервис для автоматизации внутренних процессов агентства. Интегрируется с Asana, отправляет уведомления в Telegram и обрабатывает вебхуки.

## Модули

| Модуль | Назначение |
|--------|-----------|
| `asana` | Интеграция с Asana API — задачи, проекты, вебхуки |
| `comment_notifier` | Уведомления о комментариях |
| `creative_quality` | Контроль качества креативов |
| `leave_events` | Обработка событий отпусков/отгулов |
| `message_sender` | Отправка сообщений (Telegram и др.) |
| `offboarding` | Процессы оффбординга сотрудников |
| `valentine_day` | Отдельный Telegram-бот (valentine_bot.py) |
| `vga_lands` | Лендинги / дополнительные страницы |
| `fake_message` | Генерация тестовых сообщений |
| `webhook_pinger` | Пинг и мониторинг вебхуков |

## Стек

- **Django 5** + DRF
- **Celery** + Redis (воркер + beat для периодических задач)
- **PostgreSQL**
- **Docker Compose** (web, celery_worker, celery_beat, nginx, redis, db, valentine-bot)
- **Google Sheets** (gspread) и **Telegram Bot** (python-telegram-bot)

## Запуск

```bash
cp env-example .env
# заполнить .env
docker compose up -d
```

Приложение доступно через nginx на порту из `NGINX_PORT`.
