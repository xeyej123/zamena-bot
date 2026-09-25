"""
Разовый скрипт, чтобы узнать свой chat_id.

Как пользоваться:
1. Напиши что-нибудь своему боту в Telegram (любое сообщение, например "привет").
2. Впиши свой токен ниже (или через переменную окружения BOT_TOKEN).
3. Запусти: python get_chat_id.py
4. В выводе найдёшь свой chat_id — скопируй его.
"""

import os
import requests

BOT_TOKEN = os.environ.get("BOT_TOKEN") or "ВСТАВЬ_СЮДА_СВОЙ_ТОКЕН"

resp = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates")
data = resp.json()

if not data.get("result"):
    print("Обновлений не найдено. Убедись, что ты написал боту сообщение, и попробуй снова.")
else:
    for update in data["result"]:
        chat = update["message"]["chat"]
        print(f"Имя: {chat.get('first_name')}, chat_id: {chat['id']}")
