import telebot
from config import app_token, telegram_token
from profile_api import *

bot = telebot.TeleBot(telegram_token)

def get_token(message):
    username = message.from_user.username
    if not username:
        bot.send_message(message.chat.id, text='Привет! Похоже, у тебя в телеграме не настроен никнейм. Пожалуйста, укажи его в настройках Telegrama, впиши на profile.goto.msk.ru и снова набери /start.')
    else:
        user_token = get_token_by_telegram(username)
        if not user_token:
            bot.send_message(message.chat.id, text='Не могу найти тебя на profile.goto.msk.ru :( Проверь, что ты указал никнейм в профиле и снова набери /start.')
        else:
            return user_token
    return None

def get_keyboard():
    keyboard = telebot.types.ReplyKeyboardMarkup()
    balance_button = telebot.types.InlineKeyboardButton(text="Узнать баланс")
    keyboard.add(balance_button)
    return keyboard


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_message(message.chat.id, text='Привет! Я помогу провести операции с GoToCoins!')
    user_token = get_token(message)
    if user_token:
        keyboard = get_keyboard()
        bot.send_message(message.chat.id, text='Все круто!', reply_markup=keyboard)


@bot.message_handler(content_types=['text'])
def process_message(message):
    user_token = get_token(message)
    if user_token:
        keyboard = get_keyboard()
        if message.text == 'Узнать баланс':
            balance = get_balance_by_token(user_token)
            bot.send_message(message.chat.id, text='Ваш баланс: {0} GT'.format(balance), reply_markup=keyboard)
        else:
            bot.send_message(message.chat.id, text='Я тебя не понял :(', reply_markup=keyboard)



bot.polling(none_stop=True)