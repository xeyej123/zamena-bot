# Замены занятий — Telegram-бот

Бот следит за файлом замен на сайте [ttgt.org](https://ttgt.org/images/pdf/zamena.pdf)
и присылает уведомления в Telegram. Больше не нужно вручную открывать PDF и
искать свою группу — бот сам проверяет изменения и пишет, что и на что заменили.

## Что умеет

- **Утренняя сводка** — каждый день в 8:00 по Москве приходит список замен для группы.
- **Проверка изменений** — каждый час с 9:00 до 20:00: если PDF обновился, приходит уведомление.
- **Кнопка «Проверить замены»** — проверка по запросу в любой момент, отвечает мгновенно.
- **Команды** `/start` и `/help`.

## На чём работает

Всё бесплатно и не требует постоянно включённого компьютера:

| Часть | Технология | Зачем |
|-------|-----------|-------|
| Уведомления по расписанию | **GitHub Actions** | будит скрипт по cron, парсит PDF, шлёт в Telegram |
| Кнопка в чате | **Render** (Flask + gunicorn) | принимает webhook от Telegram и мгновенно отвечает |
| Связь с Telegram | **Telegram Bot API** | отправка сообщений и приём команд |
| Разбор PDF | **pdfplumber** | достаёт текст из файла замен |
| «Не засыпать» | **GitHub Actions** | пингует Render каждые 10 минут |

Схема:

```
     iPhone / Telegram
            │
            ▼
   Telegram Bot API ──webhook──► Render (app.py)      ── кнопка «Проверить замены»
            ▲
            │
   GitHub Actions ──cron──► check_zamena.py ──► ttgt.org/zamena.pdf
       (check-zamena.yml)      (pdfplumber)
       (keep-awake.yml) ──пинг──► Render
```

## Проверка

1. Откройте бота в Telegram.
2. Отправьте `/start` — придёт приветствие с кнопкой.
3. Нажмите **«Проверить замены»** — бот скачает свежий PDF и пришлёт замены для группы.

## Настройка

Все секреты задаются в **Settings → Secrets and variables → Actions**:
`BOT_TOKEN` (токен от BotFather) и `CHAT_ID` (узнать можно через `get_chat_id.py`
или командой `/start` — бот покажет ваш chat_id).

Webhook для кнопки ставится один раз:

```
https://api.telegram.org/bot<ТОКЕН>/setWebhook?url=https://zamena-bot.onrender.com/webhook/<ТОКЕН>
```

## Файлы

| Файл | Назначение |
|------|-----------|
| `check_zamena.py` | основная логика: скачать PDF, найти замены группы, собрать сообщение |
| `app.py` | webhook-бот для Render (кнопка, `/start`, `/help`) |
| `bot.py` | тот же бот в режиме long-polling — если запускать на своём ПК/VPS |
| `get_chat_id.py` | разовый скрипт, чтобы узнать свой `chat_id` |
| `.github/workflows/check-zamena.yml` | расписание уведомлений |
| `.github/workflows/keep-awake.yml` | пинг Render + heartbeat |
| `render.yaml` | конфиг деплоя в Render |
| `requirements.txt` | зависимости Python |

## Стек

Python 3.11, Flask, gunicorn, requests, pdfplumber, Telegram Bot API,
GitHub Actions, Render.
