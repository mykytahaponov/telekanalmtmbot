import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# Встав сюди токен свого бота
BOT_TOKEN = "8304465713:AAFAYgFlKmbMTFHkxqdcb8o5jhYVeF6NyBA"

# Встановлюємо логування
logging.basicConfig(level=logging.INFO)

async def forward_and_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Виводимо chat_id у лог
    print(f"📌 CHAT ID: {update.effective_chat.id}")

    # Відповідь користувачу (або групі)
    await update.message.reply_text("Дякуємо, ваше повідомлення отримано!")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_and_reply))
    app.run_polling()
