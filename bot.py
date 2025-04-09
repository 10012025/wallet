import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, CallbackQueryHandler

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_token_txs(wallet_address):
    url = f'https://api.etherscan.io/api?module=account&action=tokentx&address={wallet_address}&sort=asc&apikey={ETHERSCAN_API_KEY}'
    try:
        response = requests.get(url)
        data = response.json()
        return data['result'] if data['status'] == '1' else []
    except Exception as e:
        print(f"Ошибка при получении токен-транзакций: {e}")
        return []

def analyze_tokens(wallet_address):
    try:
        txs = get_token_txs(wallet_address)
        print(f"DEBUG: получено {len(txs)} транзакций")
        if not txs:
            return "❌ Нет токен-транзакций или ошибка API."

        token_stats = {}
        for tx in txs:
            token = tx['tokenSymbol']
            value = int(tx['value']) / (10 ** int(tx['tokenDecimal']))
            direction = 'in' if tx['to'].lower() == wallet_address.lower() else 'out'

            if token not in token_stats:
                token_stats[token] = {'in': 0, 'out': 0}
            token_stats[token][direction] += value

        result = "📊 *Токен-статистика:*\n"
        
        for token, vals in token_stats.items():
            pnl = vals['out'] - vals['in']
            result += f"\n{token}: IN={round(vals['in'], 2)}, OUT={round(vals['out'], 2)}, PNL={round(pnl, 2)}"

        return result
    except Exception as e:
        print(f"Ошибка в analyze_tokens: {e}")
        return f"⚠️ Ошибка при анализе токенов: {e}"

def get_defi_debank(wallet_address):
    try:
        r = requests.get(f'https://openapi.debank.com/v1/user/total_balance?id={wallet_address}')
        print(f"DEBUG: Debank status = {r.status_code}")
        data = r.json()
        eth_value = data.get('total_usd_value', 0)
        return f"\n💰 DeBank: Общая стоимость портфеля: ${eth_value:.2f}"
    except Exception as e:
        print(f"Ошибка в get_defi_debank: {e}")
        return f"\n⚠️ Ошибка при получении данных с DeBank: {e}"

def start(update: Update, context: CallbackContext) -> None:
    keyboard = [[InlineKeyboardButton("🔎 Проанализировать кошелек", callback_data='analyze')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("👋 Привет! Нажми кнопку ниже, чтобы начать:", reply_markup=reply_markup)

def button_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    query.message.reply_text("📩 Отправь адрес кошелька, который нужно проанализировать.")

def handle_address(update: Update, context: CallbackContext) -> None:
    wallet = update.message.text.strip()
    update.message.reply_text("🔍 Анализирую адрес...")

    tokens_info = analyze_tokens(wallet)
    defi_info = get_defi_debank(wallet)
    final_msg = f"{tokens_info}\n\n{defi_info}"

    MAX_LENGTH = 4000
    for i in range(0, len(final_msg), MAX_LENGTH):
        update.message.reply_text(final_msg[i:i+MAX_LENGTH])

def main():
    updater = Updater(TELEGRAM_BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_callback))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_address))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
