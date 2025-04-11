import os
import openai
import logging
from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    ContextTypes, filters
)
from dotenv import load_dotenv

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Загрузка переменных окружения
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# История сообщений по user_id
user_sessions = {}

# Ограничение по количеству сообщений в истории (например, 20)
MAX_HISTORY = 20

async def chat_with_gpt(user_id, message):
    if user_id not in user_sessions:
        user_sessions[user_id] = []

    user_sessions[user_id].append({"role": "user", "content": message})
    session = user_sessions[user_id][-MAX_HISTORY:]  # обрезаем по лимиту

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=session
        )
        reply = response.choices[0].message["content"]
        user_sessions[user_id].append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        logging.error(f"Ошибка OpenAI: {e}")
        return "⚠️ Ошибка при обращении к GPT. Попробуйте позже."

# Обработка команды /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text(
    "👋 Привет! Я GPT-бот.\n\n"
    "Просто напиши мне сообщение — и я постараюсь ответить максимально умно 🤖\n\n"
    "Команда `/reset` — сброс диалога.",
    parse_mode=ParseMode.MARKDOWN
)

# Обработка команды /reset
async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_sessions[user_id] = []
    await update.message.reply_text("🧹 История диалога сброшена.")

# Обработка обычных сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text

    logging.info(f"[{user_id}] {message}")

    # Анимация "пишет..."
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    reply = await chat_with_gpt(user_id, message)

    # Отправка с поддержкой markdown
    await update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("reset", reset_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("✅ Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
