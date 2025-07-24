import os
import logging
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, filters, ContextTypes

# —————————————— Налаштування ——————————————
BOT_TOKEN   = os.environ["TELEGRAM_BOT_TOKEN"]
LOG_CHAT_ID = int(os.environ["LOG_CHAT_ID"])
WEBHOOK_URL = os.environ["WEBHOOK_URL"]  # напр.: https://telekanalmtmbot.onrender.com

# Логування
logging.basicConfig(level=logging.INFO)

# Ініціалізуємо Flask і Bot
app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher(bot, None, workers=0)

# Обробник будь-яких повідомлень
async def handle_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user    = update.effective_user
    message = update.message
    header  = (
        f"✉️ Нове повідомлення від {user.full_name} (@{user.username})\n"
        f"🆔 {user.id}  🕓 {message.date}\n"
    )

    # Текст
    if message.text:
        await bot.send_message(
            chat_id=LOG_CHAT_ID,
            text=header + f"\n📄 Текст:\n{message.text}"
        )

    # Фото
    if message.photo:
        file_id = message.photo[-1].file_id
        await bot.send_photo(
            chat_id=LOG_CHAT_ID,
            photo=file_id,
            caption=header + f"\n🖼 Фото: {message.caption or '—'}"
        )

    # Відео
    if message.video:
        file_id = message.video.file_id
        await bot.send_video(
            chat_id=LOG_CHAT_ID,
            video=file_id,
            caption=header + f"\n🎥 Відео: {message.caption or '—'}"
        )

    # Документ/інші
    if message.document:
        file_id = message.document.file_id
        await bot.send_document(
            chat_id=LOG_CHAT_ID,
            document=file_id,
            caption=header + f"\n📎 Файл: {message.document.file_name}"
        )

    # Підтвердження користувачу
    await message.reply_text("Дякуємо, ваше повідомлення отримано!")

# Регіструємо обробник
dp.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_all))

# Endpoint для webhook
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook_handler():
    update = Update.de_json(request.get_json(force=True), bot)
    dp.process_update(update)
    return "OK"

if __name__ == "__main__":
    # встановлюємо webhook при старті
    bot.set_webhook(f"{WEBHOOK_URL}/{BOT_TOKEN}")
    # запускаємо Flask
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
