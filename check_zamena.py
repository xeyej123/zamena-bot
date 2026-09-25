import os
import sys
import hashlib
import requests
import pdfplumber
from io import BytesIO

# ====== НАСТРОЙКИ (берутся из переменных окружения / GitHub Secrets) ======
BOT_TOKEN = os.environ["BOT_TOKEN"]          # токен от BotFather
CHAT_ID = os.environ["CHAT_ID"]              # твой chat_id (узнать через get_chat_id.py)
GROUP_NAME = os.environ.get("GROUP_NAME", "КС-3-1")  # твоя группа, можно поменять

PDF_URL = "https://ttgt.org/images/pdf/zamena.pdf"
HASH_FILE = "last_hash.txt"  # чтобы не слать одно и то же уведомление повторно


def send_message(text: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    resp = requests.post(url, data={"chat_id": CHAT_ID, "text": text})
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


def main():
    pdf_bytes = download_pdf()
    current_hash = hashlib.sha256(pdf_bytes).hexdigest()
    last_hash = load_last_hash()

    if current_hash == last_hash:
        print("PDF не изменился с прошлой проверки — ничего не делаем.")
        return

    save_last_hash(current_hash)

    full_text = extract_text(pdf_bytes)
    matches = find_group_lines(full_text, GROUP_NAME)

    if matches:
        message = f"⚠️ Найдены замены для группы {GROUP_NAME}:\n\n" + "\n\n".join(matches)
    else:
        message = f"Файл замен обновился, но твоей группы {GROUP_NAME} в списке нет — можно выдохнуть."

    send_message(message)
    print(message)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)
