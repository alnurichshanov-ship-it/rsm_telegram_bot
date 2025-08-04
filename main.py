import os
import requests
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

CHOOSING_CITY, INPUT_MERCH_NAME, INPUT_STORE_NAME, CHOOSE_VISIT, CHOOSE_MERCH, CHOOSE_PRICETAGS, INPUT_COMMENT = range(7)

user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name

    await update.message.reply_text("Привет! Давайте начнем анкету.")
Выберите город:",
        reply_markup=ReplyKeyboardMarkup([["Алматы", "Астана"]], resize_keyboard=True))
    return CHOOSING_CITY

async def choose_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data["city"] = update.message.text
    await update.message.reply_text("Введите ФИО мерчендайзера:", reply_markup=ReplyKeyboardRemove())
    return INPUT_MERCH_NAME

async def input_merch_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data["merch_name"] = update.message.text
    await update.message.reply_text("Введите название магазина:")
    return INPUT_STORE_NAME

async def input_store_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data["store_name"] = update.message.text
    await update.message.reply_text("Визит состоялся?", reply_markup=ReplyKeyboardMarkup([["Да", "Нет"]], resize_keyboard=True))
    return CHOOSE_VISIT

async def choose_visit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data["visit"] = update.message.text
    await update.message.reply_text("Мерчендайзер на месте?", reply_markup=ReplyKeyboardMarkup([["Да", "Нет"]], resize_keyboard=True))
    return CHOOSE_MERCH

async def choose_merch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data["merch_present"] = update.message.text
    await update.message.reply_text("Ценники?", reply_markup=ReplyKeyboardMarkup([["Да", "Нет"]], resize_keyboard=True))
    return CHOOSE_PRICETAGS

async def choose_pricetags(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data["price_tags"] = update.message.text
    await update.message.reply_text("Комментарий (можно оставить пустым):", reply_markup=ReplyKeyboardRemove())
    return INPUT_COMMENT

async def input_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data["comment"] = update.message.text
    user_data["telegram_id"] = update.effective_user.id

    # Отправка POST на Webhook
    try:
        response = requests.post(WEBHOOK_URL, json=user_data)
        if response.status_code == 200:
            await update.message.reply_text("Анкета успешно отправлена! ✅")
        else:
            await update.message.reply_text(f"Ошибка отправки: {response.text}")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_city)],
            INPUT_MERCH_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_merch_name)],
            INPUT_STORE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_store_name)],
            CHOOSE_VISIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_visit)],
            CHOOSE_MERCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_merch)],
            CHOOSE_PRICETAGS: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_pricetags)],
            INPUT_COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_comment)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
