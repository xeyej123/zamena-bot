#!/usr/bin/env python3
"""
Telegram-бот «Проверка замен» — webhook-версия (для Render / любого хостинга).

Получает обновления от Telegram через webhook и отвечает на:
  - /start                  — приветствие + кнопка
  - /help                   — справка
  - «🔄 Проверить замены»    — мгновенная проверка файла замен

Настройка:
  1. Задеплойть на Render (см. инструкцию в README/чате).
  2. Указать переменные окружения: BOT_TOKEN, GROUP_NAME.
  3. Установить webhook:
     https://api.telegram.org/bot<BOT_TOKEN>/setWebhook?url=https://<ваш-домен>/webhook/<BOT_TOKEN>
"""

import json
import os
import threading

import requests
from flask import Flask, jsonify, request

import check_zamena

BOT_TOKEN = os.environ["BOT_TOKEN"]
GROUP_NAME = os.environ.get("GROUP_NAME", "КС-3-1")

API = "https://api.telegram.org/bot" + BOT_TOKEN
CHECK_BUTTON = "🔄 Проверить замены"

KEYBOARD = {
    "keyboard": [[{"text": CHECK_BUTTON}]],
    "resize_keyboard": True,
}

app = Flask(__name__)


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
        # отвечаем webhook'у сразу, а проверку запускаем в фоне,
        # чтобы Telegram не считал запрос зависшим
        threading.Thread(target=check_now, args=(chat_id,), daemon=True).start()
    else:
        help_text(chat_id)


@app.route("/")
def index():
    return "AirPlay zamena bot is running", 200


@app.route("/webhook/<path:token>", methods=["POST"])
def webhook(token):
    if token != BOT_TOKEN:
        return jsonify({"ok": False, "error": "unauthorized"}), 403
    update = request.get_json(force=True, silent=True)
    if update:
        try:
            handle_update(update)
        except Exception as exc:
            print("Ошибка обработки обновления:", exc)
    return jsonify({"ok": True})


if __name__ == "__main__":
    # локально для проверки: python app.py (нужен BOT_TOKEN)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
