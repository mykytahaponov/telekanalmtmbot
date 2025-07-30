import os
import logging
import threading
import re
import requests
from flask import Flask, request

# —————– Конфіг з Environment —————–
BOT_TOKEN   = os.environ["TELEGRAM_BOT_TOKEN"]
LOG_CHAT_ID = os.environ["LOG_CHAT_ID"]
WEBHOOK_URL = os.environ["WEBHOOK_URL"]  # https://telekanalmtmbot.onrender.com
API_URL     = f"https://api.telegram.org/bot{BOT_TOKEN}"

# In-memory трекери стану та буферизації медіа
user_states  = {}
media_groups = {}  # media_group_id -> list of media items

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

# Health-check для UptimeRobot
@app.route("/", methods=["GET"])
def health():
    return "OK", 200

# Функція відправки зібраного альбому
def flush_media_group(group_id):
    items = media_groups.pop(group_id, [])
    if not items:
        return
    requests.post(f"{API_URL}/sendMediaGroup", json={
        "chat_id": LOG_CHAT_ID,
        "media": items
    })

# Webhook-ендпойнт
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    logging.info(f"Incoming update: {data}")

    msg = data.get("message") or data.get("edited_message")
    if not msg:
        return "OK", 200

    chat_id = msg["chat"]["id"]
    text    = msg.get("text", "")

    # 0) Обробка /reply у лог-чаті
    if text.startswith("/reply ") and msg.get("reply_to_message"):
        orig = msg["reply_to_message"].get("text", "")
        m = re.search(r"ID[: ]+(-?\d+)", orig)
        if m:
            user_id = m.group(1)
            reply_text = text[len("/reply "):]
            # Відповідаємо користувачу
            requests.post(f"{API_URL}/sendMessage", json={
                "chat_id": user_id,
                "text": reply_text
            })
            # Підтвердження у лог-чаті
            requests.post(f"{API_URL}/sendMessage", json={
                "chat_id": LOG_CHAT_ID,
                "text": f"✏️ Відповідь на повідомлення {user_id} надіслано."
            })
        else:
            requests.post(f"{API_URL}/sendMessage", json={
                "chat_id": LOG_CHAT_ID,
                "text": "❌ Не вдалося витягти ID користувача з повідомлення."
            })
        return "OK", 200

    # 1) /start → клавіатура кнопок
    if text.strip() == "/start":
        greeting = (
            "Вітаємо в офіційному телеграм-боті телеканалу МТМ!\n"
            "Керуйтесь кнопками нижче ⬇️"
        )
        keyboard = {
            "keyboard": [
                ["📄 Надіслати новину", "📋 Надіслати петицію"],
                ["❗️ Якщо знайшли помилку в матеріалі"]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }
        requests.post(f"{API_URL}/sendMessage", json={
            "chat_id": chat_id,
            "text": greeting,
            "reply_markup": keyboard
        })
        user_states.pop(chat_id, None)
        return "OK", 200

    # 2) Обробка кнопок
    if text.strip() in ("📄 Надіслати новину", "Надіслати новину"):
        requests.post(f"{API_URL}/sendMessage", json={
            "chat_id": chat_id,
            "text": "Чекаємо на вашу новину! Вона може містити текст, фото, відео або файл/документ."
        })
        user_states[chat_id] = "news"
        return "OK", 200

    if text.strip() in ("📋 Надіслати петицію", "Надіслати петицію"):
        petition_text = (
            "❗️ До нас постійно звертаються родичі загиблих Героїв з проханнями розмістити їхні петиції.\n\n"
            "Ми усвідомлюємо важливість кожного кроку. Тож публікуємо петиції, аби якомога більше "
            "запоріжців не просто ознайомились та підтримали їх, а й знали власних Героїв і Героїнь в обличчя.\n\n"
            "Надсилайте нам посилання та супроводжувальну інформацію про Героя або Героїню, "
            "і ми обовʼязково розглянемо її до публікації."
        )
        requests.post(f"{API_URL}/sendMessage", json={
            "chat_id": chat_id,
            "text": petition_text
        })
        user_states[chat_id] = "petition"
        return "OK", 200

    if text.strip() in ("❗️ Якщо знайшли помилку в матеріалі", "Якщо знайшли помилку в матеріалі"):
        error_prompt = (
            "Надсилайте нам скріншот, опис, таймкод помилки "
            "(якщо це телевізійний матеріал), і ми усунемо всі недоліки."
        )
        requests.post(f"{API_URL}/sendMessage", json={
            "chat_id": chat_id,
            "text": error_prompt
        })
        user_states[chat_id] = "error"
        return "OK", 200

    # Стан користувача
    state = user_states.get(chat_id)
    user  = msg.get("from", {})
    header = f"✉️ Нове від {user.get('first_name','')} (@{user.get('username','')})
ID: {chat_id}
"
