import os
import logging
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
)

# —————————————— Налаштування ——————————————
BOT_TOKEN   = os.environ["TELEGRAM_BOT_TOKEN"]
LOG_CHAT_ID = int(os.environ["LOG_CHAT_ID"])
WEBHOOK_URL = os.environ["WEBHOOK_URL"]  # https://<твій-сервіс>.onrender.com

# Логування
logging.basicConfig(level=logging.INFO)

# Ініціалізуємо Flask
app = Flask(__name__)

# Ініціалізуємо Telegram Application (він всередині створює Dispatcher)
application = (
    ApplicationBuilder()
    .token(BOT_TOKEN)
    .build()
)

# Функція-обробник будь-яких повідомлень
async def handle_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user    = update.effective_user
    message = update.message
    header  = (
        f"✉️ Нове повідомлення від {user.full_name} (@{user.username})\n"
        f"🆔 {user.id}  🕓 {message.date}\n"
    )

    if message.text:
        await context.bot.send_message(
            chat_id=LOG_CHAT_ID,
            text=header + f"\n📄 Текст:\n{message.text}"
        )

    if message.photo:
        file_id = message.photo[-1].file_id
        await context.bot.send_photo(
            chat_id=LOG_CHAT_ID,
            photo=file_id,
            caption=header + f"\n🖼 Фото: {message.caption or '—'}"
        )

    if message.video:
        file_id = message.video.file_id
        await context.bot.send_video(
            chat_id=LOG_CHAT_ID,
            video=file_id,
            caption=header + f"\n🎥 Відео: {message.caption or '—'}"
        )

    if message.document:
        file_id = message.document.file_id
        await context.bot.send_document(
            chat_id=LOG_CHAT_ID,
            document=file_id,
            caption=header + f"\n📎 Файл: {message.document.file_name}"
        )

    await message.reply_text("Дякуємо, ваше повідомлення отримано!")

# Регіструємо обробник
application.add_handler(
    MessageHandler(filters.ALL & ~filters.COMMAND, handle_all)
)

# HTTP-ендпойнт для webhook
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook_handler():
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)
    # передаємо апдейт у Telegram Application
    application.process_update(update)
    return "OK"

if __name__ == "__main__":
    # Встановлюємо webhook на старті
    application.bot.set_webhook(f"{WEBHOOK_URL}/{BOT_TOKEN}")
    # Піднімаємо Flask-сервер
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
