import os
import logging
import requests
from flask import Flask, request

# —————– Конфіг з Environment —————–
BOT_TOKEN   = os.environ["TELEGRAM_BOT_TOKEN"]
LOG_CHAT_ID = os.environ["LOG_CHAT_ID"]
WEBHOOK_URL = os.environ["WEBHOOK_URL"]  # https://telekanalmtmbot.onrender.com

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

# Health‐check
@app.route("/", methods=["GET"])
def health():
    return "OK", 200

# Webhook‐endpoint
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    logging.info(f"Incoming update: {data}")

    msg = data.get("message") or data.get("edited_message")
    if not msg:
        return "OK", 200

    chat_id = msg["chat"]["id"]
    text    = msg.get("text", "")

    # 1) /start → привітання з кнопками
    if text.strip() == "/start":
        greeting = (
            "Вітаємо в офіційному телеграм-боті телеканалу МТМ!\n"
            "Керуйтесь кнопками нижче ⬇️"
        )
        keyboard = {
            "keyboard": [
                ["📄 Надіслати новину"],
                ["ℹ️ Про канал", "❓ Допомога"]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }
        requests.post(f"{API_URL}/sendMessage", json={
            "chat_id": chat_id,
            "text": greeting,
            "reply_markup": keyboard
        })
        return "OK", 200

    # 2) Кнопка "Надіслати новину"
    if text.strip() == "📄 Надіслати новину" or text.strip() == "Надіслати новину":
        prompt = (
            "Чекаємо на вашу новину! "
            "Вона може містити текст, фото, відео або файл/документ."
        )
        requests.post(f"{API_URL}/sendMessage", json={
            "chat_id": chat_id,
            "text": prompt
        })
        return "OK", 200

    # 3) Будь-який контент → лог + відповідь "Прийняли на опрацювання..."
    user = msg.get("from", {})
    header = f"✉️ Нове від {user.get('first_name','')} (@{user.get('username','')})\n"

    # Логування у LOG_CHAT_ID
    if "text" in msg:
        content = msg["text"]
        requests.post(f"{API_URL}/sendMessage", json={
            "chat_id": LOG_CHAT_ID,
            "text": header + content
        })
    elif "photo" in msg:
        file_id = msg["photo"][-1]["file_id"]
        requests.post(f"{API_URL}/sendPhoto", json={
            "chat_id": LOG_CHAT_ID,
            "photo": file_id,
            "caption": header
        })
    elif "video" in msg:
        file_id = msg["video"]["file_id"]
        requests.post(f"{API_URL}/sendVideo", json={
            "chat_id": LOG_CHAT_ID,
            "video": file_id,
            "caption": header
        })
    elif "document" in msg:
        file_id = msg["document"]["file_id"]
        requests.post(f"{API_URL}/sendDocument", json={
            "chat_id": LOG_CHAT_ID,
            "document": file_id,
            "caption": header
        })

    # Відповідь користувачу
    requests.post(f"{API_URL}/sendMessage", json={
        "chat_id": chat_id,
        "text": "Прийняли на опрацювання, дякуємо!"
    })

    return "OK", 200

if __name__ == "__main__":
    # Реєстрація webhook
    resp = requests.post(f"{API_URL}/setWebhook", json={
        "url": f"{WEBHOOK_URL}/{BOT_TOKEN}"
    }).json()
    logging.info(f"setWebhook response: {resp}")

    # Запуск Flask
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
