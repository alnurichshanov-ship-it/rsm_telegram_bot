import logging
import requests
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)

# 🛠️ Укажи сюда Webhook URL от Google Apps Script
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbxE80kvIB6BzLyfllN_z8tv_VOxVtsC00qoypxvbN2iX9QoRTief49tzPDJIOIoahvp-A/exec"

# 🧭 Состояния
(CITY, FIO, SHOP_NAME, VISIT, ON_SITE, PRICE_TAGS, COMMENT) = range(7)

# 🔹 Команда /start
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
    user = update.message.from_user

    payload = {
        "telegram_id": user.id,
        "city": data.get("city"),
        "merch_name": data.get("fio"),
        "store_name": data.get("shop"),
        "visit": data.get("visit"),
        "merch_present": data.get("on_site"),
        "price_tags": data.get("price_tags"),
        "comment": data.get("comment")
    }

    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        if response.status_code == 200:
            await update.message.reply_text("✅ Данные успешно отправлены!")
        else:
            await update.message.reply_text("⚠️ Ошибка при отправке данных.")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⛔ Анкета отменена.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# 🚀 Запуск бота
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token("7961105363:AAEo5UqQ3JGTpeFJHrV2_h1WTfck17F0v9E").build()

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
