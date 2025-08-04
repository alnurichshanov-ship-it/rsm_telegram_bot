import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler,
    ContextTypes, filters
)
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 🔐 Конфигурация
BOT_TOKEN = "вставь_сюда_токен"
SHEET_NAME = "RSM Survey"
CREDENTIALS_FILE = "credentials.json"

# 🌐 Google Sheets подключение
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1

# 🧭 Состояния анкеты
(CITY, FIO, SHOP_NAME, VISIT, ON_SITE, PRICE_TAGS, COMMENT) = range(7)

# 🧵 Начало
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Давайте начнём анкету.\nВыберите город:",
        reply_markup=ReplyKeyboardMarkup([["Алматы", "Астана"]], resize_keyboard=True)
    )
    return CITY

async def get_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["city"] = update.message.text
    await update.message.reply_text("ФИО мерчендайзера:")
    return FIO

async def get_fio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["fio"] = update.message.text
    await update.message.reply_text("Название магазина:")
    return SHOP_NAME

async def get_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["shop"] = update.message.text
    await update.message.reply_text(
        "Визит состоялся?",
        reply_markup=ReplyKeyboardMarkup([["Да", "Нет"]], resize_keyboard=True)
    )
    return VISIT

async def get_visit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["visit"] = update.message.text
    await update.message.reply_text(
        "Мерчендайзер на месте?",
        reply_markup=ReplyKeyboardMarkup([["Да", "Нет"]], resize_keyboard=True)
    )
    return ON_SITE

async def get_on_site(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["on_site"] = update.message.text
    await update.message.reply_text(
        "Ценники на месте?",
        reply_markup=ReplyKeyboardMarkup([["Да", "Нет"]], resize_keyboard=True)
    )
    return PRICE_TAGS

async def get_price_tags(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["price_tags"] = update.message.text
    await update.message.reply_text("Комментарий:", reply_markup=ReplyKeyboardRemove())
    return COMMENT

async def get_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["comment"] = update.message.text
    data = context.user_data

    # запись в таблицу
    sheet.append_row([
        data.get("city"),
        data.get("fio"),
        data.get("shop"),
        data.get("visit"),
        data.get("on_site"),
        data.get("price_tags"),
        data.get("comment")
    ])

    await update.message.reply_text("✅ Спасибо, данные записаны!")
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⛔ Анкета отменена.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# 🚀 Запуск
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_city)],
            FIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_fio)],
            SHOP_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_shop)],
            VISIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_visit)],
            ON_SITE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_on_site)],
            PRICE_TAGS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_price_tags)],
            COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_comment)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()
