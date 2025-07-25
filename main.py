import os
import logging
import threading
import requests
from flask import Flask, request

# —————– Конфіг з Environment —————–
BOT_TOKEN   = os.environ["TELEGRAM_BOT_TOKEN"]
LOG_CHAT_ID = os.environ["LOG_CHAT_ID"]
WEBHOOK_URL = os.environ["WEBHOOK_URL"]  # https://telekanalmtmbot.onrender.com
API_URL     = f"https://api.telegram.org/bot{BOT_TOKEN}"

# In-memory трекери
user_states  = {}
media_groups = {}  # group_id -> list of media items

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

# Health-check для UptimeRobot
@app.route("/", methods=["GET"])
def health():
    return "OK", 200

# Функція, що відправляє зібраний альбом одним викликом
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

    # 1) /start
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

    # 2) Надіслати новину
    if text.strip() in ("📄 Надіслати новину", "Надіслати новину"):
        prompt = (
            "Чекаємо на вашу новину! "
            "Вона може містити текст, фото, відео або файл/документ."
        )
        requests.post(f"{API_URL}/sendMessage", json={
            "chat_id": chat_id,
            "text": prompt
        })
        user_states[chat_id] = "news"
        return "OK", 200

    # 3) Надіслати петицію
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

    # 4) Якщо знайшли помилку в матеріалі
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

    # Готуються до обробки контенту
    state = user_states.get(chat_id)
    user  = msg.get("from", {})
    header = f"✉️ Нове від {user.get('first_name','')} (@{user.get('username','')})\n"

    # 5) Групування media group
    if "media_group_id" in msg:
        grp_id = msg["media_group_id"]
        buffer = media_groups.setdefault(grp_id, [])
        # Визначаємо тип медіа
        if "photo" in msg:
            file_id = msg["photo"][-1]["file_id"]
            media_item = {"type": "photo", "media": file_id}
        elif "video" in msg:
            file_id = msg["video"]["file_id"]
            media_item = {"type": "video", "media": file_id}
        elif "document" in msg:
            file_id = msg["document"]["file_id"]
            media_item = {"type": "document", "media": file_id}
        else:
            return "OK", 200
        # Додаємо підпис лише до першого елементу
        if msg.get("caption") and not buffer:
            media_item["caption"] = header + msg["caption"]
        buffer.append(media_item)
        # Запускаємо таймер на відправку альбому через 1 секунду
        if len(buffer) == 1:
            threading.Timer(1.0, flush_media_group, args=(grp_id,)).start()
        # Відповідь користувачу
        if state == "petition":
            reply = "Дякуємо вам за цей важливий крок. Памʼятаємо кожного та кожну."
        elif state == "error":
            reply = "Дякуємо за увагу та вашу цікавість!"
        else:
            reply = "Прийняли на опрацювання, дякуємо!"
        requests.post(f"{API_URL}/sendMessage", json={
            "chat_id": chat_id,
            "text": reply
        })
        return "OK", 200

    # 6) Обробка одиночного контенту
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
    else:
        requests.post(f"{API_URL}/sendMessage", json={
            "chat_id": chat_id,
            "text": "Будь ласка, скористайтесь кнопками для початку."
        })
        return "OK", 200

    # Відповідь користувачу після одиночного файлу
    if state == "news":
        reply = "Прийняли на опрацювання, дякуємо!"
    elif state == "petition":
        reply = "Дякуємо вам за цей важливий крок. Памʼятаємо кожного та кожну."
    elif state == "error":
        reply = "Дякуємо за увагу та вашу цікавість!"
    else:
        reply = "Дякуємо, ваше повідомлення отримано!"

    requests.post(f"{API_URL}/sendMessage", json={
        "chat_id": chat_id,
        "text": reply
    })
    user_states.pop(chat_id, None)

    return "OK", 200

if __name__ == "__main__":
    # Реєстрація webhook
    resp = requests.post(f"{API_URL}/setWebhook", json={
        "url": f"{WEBHOOK_URL}/{BOT_TOKEN}"
    }).json()
    logging.info(f"setWebhook response: {resp}")

    # Запуск Flask-сервера
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
