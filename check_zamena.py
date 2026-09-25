import os
import sys
import json
import hashlib
import requests
import pdfplumber
from io import BytesIO

# ====== НАСТРОЙКИ (берутся из переменных окружения / GitHub Secrets) ======
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")  # токен от BotFather
CHAT_ID = os.environ.get("CHAT_ID", "")      # твой chat_id (узнать через get_chat_id.py)
GROUP_NAME = os.environ.get("GROUP_NAME", "КС-3-1")  # твоя группа, можно поменять
MODE = os.environ.get("MODE", "check")  # "daily"/"manual" — шлёт всегда, "check" — только при изменениях

PDF_URL = "https://ttgt.org/images/pdf/zamena.pdf"
HASH_FILE = "last_hash.txt"  # чтобы не слать одно и то же уведомление повторно

# кнопка в чате бота — постоянная клавиатура
KEYBOARD = {
    "keyboard": [[{"text": "🔄 Проверить замены"}]],
    "resize_keyboard": True,
}


def send_message(text: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    resp = requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text,
        "reply_markup": json.dumps(KEYBOARD),
    })
    resp.raise_for_status()


def download_pdf() -> bytes:
    resp = requests.get(PDF_URL, timeout=30)
    resp.raise_for_status()
    return resp.content


def extract_text(pdf_bytes: bytes) -> str:
    text_parts = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)
    return "\n".join(text_parts)


def find_group_lines(full_text: str, group: str) -> list[str]:
    lines = full_text.split("\n")
    matches = []
    group_norm = group.replace(" ", "").upper()
    for i, line in enumerate(lines):
        if group_norm in line.replace(" ", "").upper():
            # берём саму строку и пару строк после (там обычно детали замены)
            snippet = lines[i:i + 3]
            matches.append(" | ".join(s.strip() for s in snippet if s.strip()))
    return matches


def load_last_hash() -> str:
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            return f.read().strip()
    return ""


def save_last_hash(h: str):
    with open(HASH_FILE, "w") as f:
        f.write(h)


def build_message(matches: list[str], group: str = "", always_send: bool = True) -> str:
    group = group or GROUP_NAME
    if matches:
        prefix = "⚠️ Замены на сегодня" if always_send else "⚠️ Появились новые замены"
        return f"{prefix} для группы {group}:\n\n" + "\n\n".join(matches)
    if always_send:
        return f"На сегодня замен для группы {group} нет — можно выдохнуть."
    return f"Файл замен обновился, но твоей группы {group} в списке нет — можно выдохнуть."


def check_now(group: str = "") -> str:
    """Проверяет замены прямо сейчас и возвращает готовый текст уведомления.

    Используется ботом (bot.py) по нажатию кнопки: всегда возвращает сводку
    и не трогает файл last_hash.txt (его ведёт планировщик GitHub Actions).
    """
    pdf_bytes = download_pdf()
    full_text = extract_text(pdf_bytes)
    matches = find_group_lines(full_text, group or GROUP_NAME)
    return build_message(matches, group=group, always_send=True)


def main():
    pdf_bytes = download_pdf()
    current_hash = hashlib.sha256(pdf_bytes).hexdigest()
    last_hash = load_last_hash()
    changed = current_hash != last_hash

    if MODE == "check" and not changed:
        print("PDF не изменился с прошлой проверки — ничего не делаем.")
        return

    save_last_hash(current_hash)

    full_text = extract_text(pdf_bytes)
    matches = find_group_lines(full_text, GROUP_NAME)

    message = build_message(matches, always_send=(MODE != "check"))
    send_message(message)
    print(message)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)
