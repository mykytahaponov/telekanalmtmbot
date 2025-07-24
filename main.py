import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
)

# —————– Налаштування з Environment —————–
BOT_TOKEN   = os.environ["TELEGRAM_BOT_TOKEN"]
LOG_CHAT_ID = int(os.environ["LOG_CHAT_ID"])
WEBHOOK_URL = os.environ["WEBHOOK_URL"]  # напр.: https://telekanalmtmbot.onrender.com

# Логування в консолі Render
logging.basicConfig(level=logging.INFO)

# Обробник усіх вхідних повідомлень
async def handle_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    msg  = update.message
    logging.info(f"Got update in chat {chat.id}: {msg}")
    # Пересилаємо в лог-чат
    header = f"✉️ Нове від {user.full_name} (@{user.username}) • {msg.date}\n"
    if msg.text:
        await context.bot.send_message(LOG_CHAT_ID, header + msg.text)
    elif msg.photo:
        await context.bot.send_photo(LOG_CHAT_ID, msg.photo[-1].file_id, caption=header)
    elif msg.video:
        await context.bot.send_video(LOG_CHAT_ID, msg.video.file_id, caption=header)
    elif msg.document:
        await context.bot.send_document(LOG_CHAT_ID, msg.document.file_id, caption=header)
    # Підтвердження в тому ж чаті
    await msg.reply_text("Дякуємо, ваше повідомлення отримано!")

# Будуємо Bot
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_all))

if __name__ == "__main__":
    # Запускаємо вбудований webhook‐сервер
    port = int(os.environ.get("PORT", 10000))
    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=BOT_TOKEN,  
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}"
    )
