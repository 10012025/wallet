import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, CallbackQueryHandler

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получение общей статистики через DeBank (или мок, если API ограничен)
def get_wallet_summary(address):
    try:
        # Пример запроса к DeBank (без авторизации, если возможно)
        debank_url = f"https://openapi.debank.com/v1/user/total_balance?id={address}"
        r = requests.get(debank_url)
        data = r.json()
        total_usd = data.get("total_usd_value", 0)

        # Эти данные в реальности нужно получать с других endpoints или агрегировать самостоятельно
        # Здесь просто примеры — заглушки
        summary = {
            "Общая прибыль": "$288,661",
            "Реализованный": "$43K (0.41%)",
            "Нереализованный": "-$13,060.6 (-0.13%)",
            "Внешний": "$246K",
            "Win Rate": "86.99%",
            "Побед": "2,407",
            "Проигрышей": "360",
            "Объем торгов": "$34M",
            "Торгов": "661,315",
            "Средний размер сделки": "51,642",
            "Total Value (по DeBank)": f"${total_usd:,.2f}"
        }

        # Формируем текст ответа
        msg = (
            f"📊 <b>Сводка по кошельку</b>"
            f"
<b>Общая прибыль:</b> {summary['Общая прибыль']}"
            f"
├ Реализованный: {summary['Реализованный']}"
            f"
├ Нереализованный: {summary['Нереализованный']}"
            f"
└ Внешний: {summary['Внешний']}"
            f"

<b>Win Rate:</b> {summary['Win Rate']}"
            f"
├ Побед: {summary['Побед']}"
            f"
└ Поражений: {summary['Проигрышей']}"
            f"

<b>Объем торгов:</b> {summary['Объем торгов']}"
            f"
├ Кол-во торгов: {summary['Торгов']}"
            f"
└ Средний размер: {summary['Средний размер сделки']}"
            f"

📦 <b>По данным DeBank:</b> {summary['Total Value (по DeBank)']}"
        )

        return msg
    except Exception as e:
        logger.error(f"Ошибка при получении сводки: {e}")
        return "⚠️ Ошибка при получении сводки."

def start(update: Update, context: CallbackContext) -> None:
    keyboard = [[InlineKeyboardButton("📊 Сводка по кошельку", callback_data='summary')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("👋 Привет! Нажми кнопку, чтобы получить сводку по кошельку:", reply_markup=reply_markup)

def button_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    query.message.reply_text("📩 Введи адрес кошелька для сводки:")

def handle_wallet(update: Update, context: CallbackContext) -> None:
    address = update.message.text.strip()
    update.message.reply_text("🔍 Получаю сводку...")

    summary = get_wallet_summary(address)
    MAX_LENGTH = 4000
    for i in range(0, len(summary), MAX_LENGTH):
        update.message.reply_text(summary[i:i+MAX_LENGTH], parse_mode="HTML")

def main():
    updater = Updater(TELEGRAM_BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_callback))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_wallet))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
