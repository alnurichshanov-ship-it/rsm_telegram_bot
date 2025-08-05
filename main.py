import logging
import requests
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes

# --- ВСТАВЬ СЮДА СВОЙ ТОКЕН ---
TELEGRAM_BOT_TOKEN = '7961105363:AAEo5UqQ3JGTpeFJHrV2_h1WTfck17F0v9E'
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbwJmHrBXep8JLUadTvporyxy_mYJYByYnkYqvRbTqkQVjn7r8xGS7QJNYaJYsCgdB-E/exec"
GOOGLE_SHEET_LINK = "https://docs.google.com/spreadsheets/AKfycbwJmHrBXep8JLUadTvporyxy_mYJYByYnkYqvRbTqkQVjn7r8xGS7QJNYaJYsCgdB-E/edit"  # по желанию, для админов

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Состояния
(CITY, NAME, STORE, VISIT, PRESENT, TAGS, COMMENT) = range(7)

# --- Фиктивная база пользователей (заменить чтением из Google Sheets при желании)
USERS = {
    "123456789": {"name": "Иван", "status": "RSM"},
    "987654321": {"name": "Анна", "status": "Admin"},
}

# --- /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    # Проверка в базе
    user = USERS.get(user_id)

    if user:
        if user["status"] == "RSM":
            await update.message.reply_text("Привет! Начнём анкету. В каком ты городе?")
            return CITY
        elif user["status"] == "Admin":
            await update.message.reply_text(f"👋 Привет, админ!\nВот ссылка на таблицу:\n{GOOGLE_SHEET_LINK}")
            return ConversationHandler.END
    else:
        await update.message.reply_text("Ты не зарегистрирован. Введи ФИО для заявки:")
        context.user_data["status"] = "pending"
        return NAME

# --- Шаги анкеты
async def city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["city"] = update.message.text
    await update.message.reply_text("ФИО мерчендайзера?")
    return NAME

async def name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("status") == "pending":
        # Отправка заявки на регистрацию
        payload = {
            "telegram_id": update.effective_user.id,
            "full_name": update.message.text,
            "status": "Pending"
        }
        requests.post(WEBHOOK_URL, json=payload)
        await update.message.reply_text("📩 Заявка отправлена. Ожидай одобрения.")
        return ConversationHandler.END
    context.user_data["merch_name"] = update.message.text
    await update.message.reply_text("Название магазина?")
    return STORE

async def store(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["store_name"] = update.message.text
    reply_keyboard = [["Да", "Нет"]]
    await update.message.reply_text("Визит состоялся?", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return VISIT

async def visit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["visit"] = update.message.text
    reply_keyboard = [["Да", "Нет"]]
    await update.message.reply_text("Мерчендайзер на месте?", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return PRESENT

async def present(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["merch_present"] = update.message.text
    reply_keyboard = [["Да", "Нет"]]
    await update.message.reply_text("Ценники есть?", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return TAGS

async def tags(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["price_tags"] = update.message.text
    await update.message.reply_text("Комментарий?", reply_markup=ReplyKeyboardRemove())
    return COMMENT

async def comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["comment"] = update.message.text

    # Подготовка данных
    payload = {
        "telegram_id": update.effective_user.id,
        "city": context.user_data["city"],
        "merch_name": context.user_data["merch_name"],
        "store_name": context.user_data["store_name"],
        "visit": context.user_data["visit"],
        "merch_present": context.user_data["merch_present"],
        "price_tags": context.user_data["price_tags"],
        "comment": context.user_data["comment"],
    }

    # Отправка
    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        if response.status_code == 200:
            await update.message.reply_text("✅ Данные отправлены!")
        else:
            await update.message.reply_text(f"⚠️ Ошибка при отправке: {response.text}")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка сети: {e}")

    return ConversationHandler.END

# --- Отмена
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Опрос отменён.")
    return ConversationHandler.END

# --- Главная функция
def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, city)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
            STORE: [MessageHandler(filters.TEXT & ~filters.COMMAND, store)],
            VISIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, visit)],
            PRESENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, present)],
            TAGS: [MessageHandler(filters.TEXT & ~filters.COMMAND, tags)],
            COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, comment)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
