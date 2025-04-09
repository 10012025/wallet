import os
import logging
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_token_txs(wallet_address):
    url = f'https://api.etherscan.io/api?module=account&action=tokentx&address={wallet_address}&sort=asc&apikey={ETHERSCAN_API_KEY}'
    response = requests.get(url)
    data = response.json()
    return data['result'] if data['status'] == '1' else []

def analyze_tokens(wallet_address):
    txs = get_token_txs(wallet_address)
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
        result += f"\n*{token}*: 🔽 {round(vals['in'], 2)} | 🔼 {round(vals['out'], 2)} | 🧮 PNL: {round(pnl, 2)}"

    return result

def get_defi_debank(wallet_address):
    try:
        r = requests.get(f'https://openapi.debank.com/v1/user/total_balance?id={wallet_address}')
        data = r.json()
        eth_value = data.get('total_usd_value', 0)
        return f"💰 *DeBank*: Общая стоимость портфеля: ${eth_value:.2f}"
    except:
        return "❌ Ошибка при получении данных с DeBank."

def analyze(update: Update, context: CallbackContext) -> None:
    if not context.args:
        update.message.reply_text("ℹ️ Использование: /analyze <адрес_кошелька>")
        return

    wallet = context.args[0]
    update.message.reply_text("🔍 Анализирую адрес...")

    tokens_info = analyze_tokens(wallet)
    defi_info = get_defi_debank(wallet)

    final_msg = f"{tokens_info}\n\n{defi_info}"
    update.message.reply_text(final_msg, parse_mode="Markdown")

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("👋 Привет! Отправь команду:\n/analyze <адрес кошелька>")

def main():
    updater = Updater(TELEGRAM_BOT_TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("analyze", analyze))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
