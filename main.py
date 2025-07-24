import os
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
)

# —————————————— Налаштування ——————————————
BOT_TOKEN   = os.environ["TELEGRAM_BOT_TOKEN"]
LOG_CHAT_ID = int(os.environ["LOG_CHAT_ID"])
WEBHOOK_URL = os.environ["WEBHOOK_URL"]

# Логування
logging.basicConfig(level=logging.INFO)

# Flask app
app = Flask(__name__)

# Telegram Application
application = (
    ApplicationBuilder()
    .token(BOT_TOKEN)
    .build()
)

# Обробник усіх повідомлень
async def handle_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message

    if not message:
        return

    header = f"✉️ Нове повідомлення від {user.full_name} (@{user.username})\n🆔 {user.id}  🕓 {message.date}\n"

    if message.text:
        await context.bot.send_message(chat_id=LOG_CHAT_ID, text=header + f"\n📄 Текст:\n{message.text}")
        await message.reply_text("Дякуємо, ваше повідомлення отримано!")

    elif message.photo:
        await context.bot.send_photo(chat_id=LOG_CHAT_ID, photo=message.photo[-1].file_id, caption=header)
        await message.reply_text("Фото отримано!")

    elif message.video:
        await context.bot.send_video(chat_id=LOG_CHAT_ID, video=message.video.file_id, caption=header)
        await message.reply_text("Відео отримано!")

    elif message.document:
        await context.bot.send_document(chat_id=LOG_CHAT_ID, document=message.document.file_id, caption=header)
        await message.reply_text("Файл отримано!")

# Регістрація обробника
application.add_handler(
    MessageHandler(filters.ALL & ~filters.COMMAND, handle_all)
)

# Flask endpoint
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook_handler():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.create_task(application.process_update(update))
    return "OK"

# Старт
if __name__ == "__main__":
    application.bot.set_webhook(f"{WEBHOOK_URL}/{BOT_TOKEN}")
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
