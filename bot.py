#!/usr/bin/env python3
"""
Telegram-бот «Проверка замен» (режим long-polling).

Отвечает на:
  - /start                  — приветствие + кнопка
  - /help                   — справка
  - «🔄 Проверить замены»    — мгновенная проверка файла замен

Запуск:  BOT_TOKEN=... python3 bot.py
Бот должен работать постоянно (VPS, Raspberry Pi, домашний ПК или systemd-служба).

Требования: requests, pdfplumber (см. requirements.txt).
"""

import json
import os
import time

import requests

import check_zamena

BOT_TOKEN = os.environ["BOT_TOKEN"]
GROUP_NAME = os.environ.get("GROUP_NAME", "КС-3-1")

API = "https://api.telegram.org/bot" + BOT_TOKEN
CHECK_BUTTON = "🔄 Проверить замены"

KEYBOARD = {
    "keyboard": [[{"text": CHECK_BUTTON}]],
    "resize_keyboard": True,
}


def send_message(chat_id, text):
    resp = requests.post(
        API + "/sendMessage",
        data={"chat_id": chat_id, "text": text, "reply_markup": json.dumps(KEYBOARD)},
        timeout=30,
    )
    resp.raise_for_status()


def greeting(chat_id):
    send_message(
        chat_id,
        "Привет! Я слежу за заменами занятий.\n\n"
        f"Твоя группа: {GROUP_NAME}\n"
        f"Твой chat_id: {chat_id}\n\n"
        "Нажми «🔄 Проверить замены», чтобы узнать замены прямо сейчас.\n"
        "Автоматические уведомления приходят по расписанию.",
    )


def help_text(chat_id):
    send_message(
        chat_id,
        "Доступные команды:\n"
        "/start — приветствие и кнопка\n"
        "/help — эта справка\n\n"
        "Или нажми кнопку «🔄 Проверить замены», чтобы проверить прямо сейчас.",
    )


def check_now(chat_id):
    send_message(chat_id, "⏳ Проверяю файл замен…")
    try:
        result = check_zamena.check_now(GROUP_NAME)
    except Exception as exc:
        result = f"Не удалось проверить замены: {exc}"
    send_message(chat_id, result)


def handle_update(update):
    message = update.get("message") or update.get("edited_message")
    if not message:
        return
    text = (message.get("text") or "").strip()
    chat_id = message["chat"]["id"]

    if text == "/start":
        greeting(chat_id)
    elif text == "/help":
        help_text(chat_id)
    elif text == CHECK_BUTTON:
        check_now(chat_id)
    else:
        help_text(chat_id)


def main():
    offset = 0
    print("Бот запущен. Ожидаю сообщения (Ctrl+C для выхода)…")
    while True:
        try:
            updates = (
                requests.get(
                    API + "/getUpdates",
                    params={"timeout": 30, "offset": offset},
                    timeout=60,
                ).json().get("result", [])
            )
            for update in updates:
                offset = update["update_id"] + 1
                try:
                    handle_update(update)
                except Exception as exc:
                    print("Ошибка обработки обновления:", exc)
        except KeyboardInterrupt:
            print("\nОстановлено.")
            break
        except requests.RequestException as exc:
            print("Сетевая ошибка:", exc, "— повтор через 5 сек.")
            time.sleep(5)
        except Exception as exc:
            print("Ошибка:", exc, "— повтор через 5 сек.")
            time.sleep(5)


if __name__ == "__main__":
    main()
