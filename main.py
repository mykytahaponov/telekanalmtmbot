import os
import logging
import requests
from flask import Flask, request

# —————– Конфіг з Environment —————–
BOT_TOKEN   = os.environ["TELEGRAM_BOT_TOKEN"]
LOG_CHAT_ID = os.environ["LOG_CHAT_ID"]        # рядок, тому без int()
WEBHOOK_URL = os.environ["WEBHOOK_URL"]        # напр.: https://telekanalmtmbot.onrender.com

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Логи
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Health-check для UptimeRobot
@app.route("/", methods=["GET"])
def health():
    return "OK", 200

# Webhook-endpoint, куди дзвонить Telegram
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    logging.info(f"Incoming update: {data}")

    message = data.get("message") or data.get("edited_message")
    if not message:
        return "OK", 200

    chat_id = message["chat"]["id"]
    # Збираємо заголовок для лог-чату
    user = message.get("from", {})
    header = f"✉️ Нове від {user.get('first_name','')} (@{user.get('username','')})\n"

    # 1) Пересилаємо в лог-чат
    if "text" in message:
        text = message["text"]
        requests.post(f"{API_URL}/sendMessage", json={
            "chat_id": LOG_CHAT_ID,
            "text": header + text
        })
    elif "photo" in message:
        file_id = message["photo"][-1]["file_id"]
        requests.post(f"{API_URL}/sendPhoto", json={
            "chat_id": LOG_CHAT_ID,
            "photo": file_id,
            "caption": header
        })
    elif "video" in message:
        file_id = message["video"]["file_id"]
        requests.post(f"{API_URL}/sendVideo", json={
            "chat_id": LOG_CHAT_ID,
            "video": file_id,
            "caption": header
        })
    elif "document" in message:
        file_id = message["document"]["file_id"]
        requests.post(f"{API_URL}/sendDocument", json={
            "chat_id": LOG_CHAT_ID,
            "document": file_id,
            "caption": header
        })

    # 2) Відповідаємо користувачу
    requests.post(f"{API_URL}/sendMessage", json={
        "chat_id": chat_id,
        "text": "Дякуємо, ваше повідомлення отримано!"
    })

    return "OK", 200

if __name__ == "__main__":
    # РЕЄСТРАЦІЯ WEBHOOK (докидаємо токен в URL)
    set_webhook = requests.post(f"{API_URL}/setWebhook", json={
        "url": f"{WEBHOOK_URL}/{BOT_TOKEN}"
    }).json()
    logging.info(f"setWebhook response: {set_webhook}")

    # Запускаємо Flask
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
