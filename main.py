import os
import asyncio
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
)

# —————– Конфіг з Environment —————–
BOT_TOKEN   = os.environ["TELEGRAM_BOT_TOKEN"]
LOG_CHAT_ID = int(os.environ["LOG_CHAT_ID"])
WEBHOOK_URL = os.environ["WEBHOOK_URL"]  # напр.: https://telekanalmtmbot.onrender.com

# Логи
logging.basicConfig(level=logging.INFO)

# Ініціалізуємо Flask
app = Flask(__name__)

# Ініціалізуємо бота
application = ApplicationBuilder().token(BOT_TOKEN).build()
application.add_handler(
    MessageHandler(filters.ALL & ~filters.COMMAND, 
                   lambda u, c: asyncio.create_task(handle_all(u, c)))
)

async def handle_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    msg  = update.message
    user = update.effective_user
    logging.info(f"Got update in chat {chat.id}: {msg}")

    header = f"✉️ Нове від {user.full_name} (@{user.username}) • {msg.date}\n"
    if msg.text:
        await context.bot.send_message(LOG_CHAT_ID, header + msg.text)
        await msg.reply_text("Дякуємо, ваше повідомлення отримано!")
    elif msg.photo:
        await context.bot.send_photo(LOG_CHAT_ID, msg.photo[-1].file_id, caption=header)
        await msg.reply_text("Фото отримано!")
    elif msg.video:
        await context.bot.send_video(LOG_CHAT_ID, msg.video.file_id, caption=header)
        await msg.reply_text("Відео отримано!")
    elif msg.document:
        await context.bot.send_document(LOG_CHAT_ID, msg.document.file_id, caption=header)
        await msg.reply_text("Файл отримано!")

# Health-check для UptimeRobot
@app.route("/", methods=["GET"])
def health():
    return "OK", 200

# Endpoint вебхуку
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook_handler():
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)
    # обробка у фоновому таску
    asyncio.create_task(application.process_update(update))
    return "OK", 200

if __name__ == "__main__":
    # реєструємо вебхук
    application.bot.set_webhook(f"{WEBHOOK_URL}/{BOT_TOKEN}")
    # запускаємо Flask
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
