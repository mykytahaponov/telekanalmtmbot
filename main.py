import os
import logging
import asyncio
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN    = os.environ["TELEGRAM_BOT_TOKEN"]
LOG_CHAT_ID  = int(os.environ["LOG_CHAT_ID"])
WEBHOOK_URL  = os.environ["WEBHOOK_URL"]  # https://<your>.onrender.com

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

application = (
    ApplicationBuilder()
    .token(BOT_TOKEN)
    .build()
)

# Обробник
async def handle_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message
    header = (
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

# Додаємо хендлер
application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_all))

# Webhook endpoint
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook_handler():
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)

    # Правильно запускати обробку в асинхронному loop
    asyncio.create_task(application.process_update(update))

    return "OK"

if __name__ == "__main__":
    # Встановлюємо webhook і запускаємо Flask
    async def setup():
        await application.initialize()
        await application.bot.set_webhook(f"{WEBHOOK_URL}/{BOT_TOKEN}")
        await application.start()
        await application.updater.start_polling()  # не запускає polling, але потрібне для контексту
        print("✅ Webhook set")

    asyncio.get_event_loop().run_until_complete(setup())
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
