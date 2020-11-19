import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from coingecko import CoingeckoApi
import pickle
import locale
import os
import sys

try:
    from api_token import token
except ModuleNotFoundError:
    print('File "api_token.py" does not exist!')
    sys.exit(1)
except ImportError:
    print('File "api_token.py" does not contain the token!')
    sys.exit(1)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)
if not os.path.isfile('data.pickle'):
    portfolios = {}
else:
    with open('data.pickle', 'rb') as f:
        portfolios = pickle.load(f)
old_balances = {}
min_changes = {}
api = CoingeckoApi()


def add(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    if len(context.args) != 2:
        update.message.reply_text('Usage: /add <symbol> <balance>')
        return
    currency = context.args[0]
    if not api.is_valid_id(currency):
        update.message.reply_text('Parameter <symbol> is no valid id! Check out https://api.coingecko.com/api/v3/coins/list')
        return
    try:
        balance = float(context.args[1])
    except ValueError:
        update.message.reply_text('Parameter <balance> is no valid float value!')
        return

    if chat_id not in portfolios:
        portfolios[chat_id] = {}
    portfolios[chat_id][currency] = balance
    with open('data.pickle', 'wb') as f:
        pickle.dump(portfolios, f, pickle.HIGHEST_PROTOCOL)
    update.message.reply_text('Portfolio updated successfully!')


def balance(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    if chat_id not in portfolios:
        update.message.reply_text('Your portfolio is empty! Use /add <symbol> <balance>')
        return

    val = api.get_portfolio_value(portfolios[chat_id])
    text = locale.format_string("Portfolio: %.2f€", val, grouping=True)
    update.message.reply_text(text)


def notify_proc(context):
    job = context.job
    chat_id = job.context
    if chat_id not in portfolios:
        context.bot.send_message(chat_id, text='Your portfolio is empty! Use /add <symbol> <balance>')
        return

    val = api.get_portfolio_value(portfolios[chat_id])
    old_val = old_balances[chat_id]
    change = ((val / old_val) - 1) * 100
    emoji = ("\U0001F680" if change > 0 else "\U0001F4A9")
    text = locale.format_string("Portfolio: %.2f€ %+.2f%% %s", (val, change, emoji), grouping=True)
    if abs(change) >= min_changes[chat_id]:
        context.bot.send_message(chat_id, text=text)
        old_balances[chat_id] = val


def notify(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    if chat_id not in portfolios:
        update.message.reply_text('Your portfolio is empty! Use /add <symbol> <balance>')
        return

    if len(context.args) != 1:
        update.message.reply_text('Usage: /notify <min_change>')
        return

    try:
        min_change = float(context.args[0])
    except ValueError:
        update.message.reply_text('Parameter <min_change> is no valid float value!')
        return

    min_changes[chat_id] = min_change
    old_balances[chat_id] = api.get_portfolio_value(portfolios[chat_id])
    context.job_queue.run_repeating(notify_proc, interval=10, context=chat_id, name=str(chat_id))
    update.message.reply_text('Notifications activated!')


def main():
    updater = Updater(token, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("balance", balance))
    dispatcher.add_handler(CommandHandler("add", add))
    dispatcher.add_handler(CommandHandler("notify", notify))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
