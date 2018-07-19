import telebot
import time
import emoji

from config import app_token, telegram_token, socks_string
from profile_api import *
import os.path


telebot.apihelper.proxy = {'https': socks_string}

if (not os.path.isfile('base.json')):
    with open('base.json', 'w') as f:
        f.write('{}')

bot = telebot.TeleBot(telegram_token)
bot.remove_webhook()

shop_storage = {}
temp_storage = {}
answer_cache = {}

def find_telegram_by_id(id):
    try:
        with open('base.json') as file:
            base = json.loads(file.read())
        if id in base:
            return base[id]
        return None
    except:
        return None

def get_history(token):
    history = get_history_by_token(token)
    text = ":clipboard: История начислений:\n\n"

    if len(history) == 0:
        text += ":x: Начислений пока нет."

    for record in history[::-1]:
        name = record["userFrom"]['firstName'] + " " + record["userFrom"]['lastName']
        comment = record["comment"]
        count = record["count"]

        text = text + ":dollar: {} ({}, {})\n".format(count, comment, name)

    return text

def add_telegram_to_base(id, telegram_id):
    try:
        with open('base.json') as file:
            base = json.loads(file.read())
        base[id] = telegram_id
        with open('base.json', 'w') as file:
            file.write(json.dumps(base))
    except:
        pass

def get_token(message):
    username = message.from_user.username
    if not username:
        bot.send_message(message.chat.id, text='Привет! Похоже, у тебя в телеграме не настроен никнейм. Пожалуйста, укажи его в настройках Telegrama, впиши на profile.goto.msk.ru и снова набери /start.')
    else:
        user_token = get_token_by_telegram(username)
        if not user_token:
            keyboard = telebot.types.InlineKeyboardMarkup()
            url = "https://profile.goto.msk.ru/workspace/settings"
            url_button = telebot.types.InlineKeyboardButton(text="Перейти в настройки", url=url)
            keyboard.add(url_button)
            bot.send_message(message.chat.id, text='Не могу найти тебя на profile.goto.msk.ru :(', reply_markup=telebot.types.ReplyKeyboardRemove())
            bot.send_message(message.chat.id, 'Проверь, что ты указал никнейм в профиле и снова набери /start.', reply_markup=keyboard)
        else:
            return user_token
    return None


def get_keyboard(is_admin = False):
    keyboard = telebot.types.ReplyKeyboardMarkup()
    balance_button = telebot.types.KeyboardButton(text="Узнать баланс")
    shop_button = telebot.types.KeyboardButton(text="Магазин")
    if is_admin:
        add_button = telebot.types.KeyboardButton(text="Начислить")
        keyboard.add(add_button)
    keyboard.add(balance_button)
    keyboard.add(shop_button)
    return keyboard

def get_add_keyboard(students):
    keyboard = telebot.types.InlineKeyboardMarkup()
    for student in students:
        name = student['user']['firstName'] + " " + student['user']['lastName']
        balance = student['user']['gotoCoins']
        id = student['user']['profileId']
        student_button = telebot.types.InlineKeyboardButton(text="{} ({} GT)".format(name, balance), callback_data="add_{0}".format(id))
        keyboard.add(student_button)
    return keyboard

def get_shop_keyboard():
    keyboard = telebot.types.InlineKeyboardMarkup()
    goods = get_goods()
    for good in goods:
        name = good['title']
        price = good['price']
        id = good['id']
        button = telebot.types.InlineKeyboardButton(text="{} ({} GT)".format(name, price), callback_data="buy_{0}".format(id))
        keyboard.add(button)
    button = telebot.types.InlineKeyboardButton(text="Я просто смотрю...",
                                                callback_data="cancel")
    keyboard.add(button)
    return keyboard

def get_confirm_keyboard():
    keyboard = telebot.types.InlineKeyboardMarkup()
    yes_button = telebot.types.InlineKeyboardButton(text="Да", callback_data="yes")
    no_button = telebot.types.InlineKeyboardButton(text="Нет", callback_data="no")
    keyboard.add(yes_button)
    keyboard.add(no_button)
    return keyboard

def process_money(message):
    user_token = get_token(message)
    is_admin = get_permissions_by_token(user_token)
    keyboard = get_keyboard(is_admin)
    try:
        if not is_admin:
            raise Exception("no permissions")
        money = int(message.text)
        if money == 0 or abs(money) > 1000:
            raise Exception("overlimit")
        temp_storage[message.chat.id]['money'] = money
        answer = bot.send_message(message.chat.id, text=emoji.emojize(':bar_chart: За что начисляем GT?', use_aliases=True))
        bot.register_next_step_handler(answer, process_comment)
    except Exception as e:
        answer = bot.send_message(message.chat.id, text=emoji.emojize(':confused: Окей, отмена.',  use_aliases=True), reply_markup=keyboard)
        bot.register_next_step_handler(answer, process_command)

def process_comment(message):
    user_token = get_token(message)
    is_admin = get_permissions_by_token(user_token)
    keyboard = get_keyboard(is_admin)
    try:
        if not is_admin:
            raise Exception("no permissions")
        comment = message.text
        temp_storage[message.chat.id]['comment'] = comment
        temp_storage[message.chat.id]['token'] = user_token
        id = temp_storage[message.chat.id]['id']
        money = temp_storage[message.chat.id]['money']
        name = get_name_by_id(id)
        bot.send_message(message.chat.id, text=emoji.emojize(':customs: Начисляем {} GT для {} за "{}"?'.format(money, name, comment), use_aliases=True), reply_markup=get_confirm_keyboard())
    except Exception as e:
        answer = bot.send_message(message.chat.id, text='Что-то пошло не по плану - опять все перепутали :(.', reply_markup=keyboard)
        bot.register_next_step_handler(answer, process_command)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_message(message.chat.id, text=emoji.emojize(':boar: Привет! Я помогу провести операции с GoToCoins! Секундочку...', use_aliases=True))
    user_token = get_token(message)
    id = get_id_by_token(user_token)
    if user_token:
        add_telegram_to_base(id, message.chat.id)
        keyboard = get_keyboard(get_permissions_by_token(user_token))
        answer = bot.send_message(message.chat.id, text=emoji.emojize(':thumbsup: Я готов к работе. В любой непонятной ситуации жми /start.', use_aliases=True), reply_markup=keyboard)
        bot.register_next_step_handler(answer, process_command)


def process_command(message):
    user_token = get_token(message)
    if user_token:
        is_admin = get_permissions_by_token(user_token)
        keyboard = get_keyboard(is_admin)
        if message.text == 'Узнать баланс':
            balance = get_balance_by_token(user_token)
            text = emoji.emojize(':moneybag: Ваш баланс: {0} GT \n\n'.format(balance) + get_history(user_token), use_aliases=True)
            answer = bot.send_message(message.chat.id, text=text, reply_markup=keyboard)
            bot.register_next_step_handler(answer, process_command)
        elif message.text == 'Начислить' and is_admin:
            bot.send_message(message.chat.id, text=emoji.emojize(':money_with_wings: Начисляем GT.', use_aliases=True), reply_markup=telebot.types.ReplyKeyboardRemove())
            process_add_command(message)
            #bot.register_next_step_handler()
        elif message.text == 'Магазин':
            process_shop_command(message, user_token)
        else:
            answer = bot.send_message(message.chat.id, text=emoji.emojize(':worried: Я тебя не понял :(', use_aliases=True), reply_markup=keyboard)
            bot.register_next_step_handler(answer, process_command)

def process_add_command(message):
    user_token = get_token(message)
    if user_token:
        text = message.text
        '''
        if message.text == 'Начислить':
            text = ''
        '''
        if message.chat.id in answer_cache:
            bot.edit_message_text(chat_id=message.chat.id, message_id=answer_cache[message.chat.id],
                                      text=emoji.emojize(':eyes: Ищем участника...', use_aliases=True))
        students = get_students_by_token(user_token)
        students = filter(lambda x: text.lower() in (x['user']['firstName'] + " " + x['user']['lastName']).lower(), students)
        keyboard = get_add_keyboard(students)
        answer = bot.send_message(message.chat.id, text=emoji.emojize(':runner: Выберите участника или начните вводить его имя: ', use_aliases=True), reply_markup=keyboard)
        bot.register_next_step_handler(answer, process_add_command)
        answer_cache[message.chat.id] = answer.message_id

def process_shop_command(message, user_token):
    if user_token:
        keyboard = get_shop_keyboard()
        shop_storage[message.chat.id] = user_token
        bot.send_message(message.chat.id, text=emoji.emojize(':raising_hand: Что покупаем?', use_aliases=True), reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        try:
            if call.data.startswith("add"):
                id = call.data.split('_')[1]
                temp_storage[call.message.chat.id] = {}
                temp_storage[call.message.chat.id]['id'] = id
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=emoji.emojize(":credit_card: Укажите, сколько GT нужно начислить или введите 0 для отмены.", use_aliases=True))
                bot.clear_step_handler(call.message)
                bot.register_next_step_handler(call.message, process_money)
            elif call.data.startswith("buy"):
                item = call.data.split('_')[1]
                user_token = shop_storage[call.message.chat.id]
                if not user_token:
                    raise Exception("no token")
                is_admin = get_permissions_by_token(user_token)
                keyboard = get_keyboard(is_admin)
                shop_storage[call.message.chat.id] = None
                if make_buy(user_token, item):
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                          text=emoji.emojize(':white_check_mark: Платеж прошел, ожидайте доставку!', use_aliases=True))
                else:
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=emoji.emojize(':cry: Недостаточно средств или товар закончился.', use_aliases=True),  reply_markup=keyboard)
                answer = bot.send_message(call.message.chat.id, "Что дальше?", reply_markup=keyboard)
                bot.register_next_step_handler(answer, process_command)
            elif call.data.startswith("cancel"):
                user_token = shop_storage[call.message.chat.id]
                if not user_token:
                    raise Exception("no token")
                is_admin = get_permissions_by_token(user_token)
                keyboard = get_keyboard(is_admin)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text=emoji.emojize(':new_moon_with_face: Нет, так нет.', use_aliases=True))
                answer = bot.send_message(call.message.chat.id, "Что дальше?", reply_markup=keyboard)
                bot.register_next_step_handler(answer, process_command)


            elif call.data == "yes":
                comment = temp_storage[call.message.chat.id]['comment']
                id = temp_storage[call.message.chat.id]['id']
                money = temp_storage[call.message.chat.id]['money']
                user_token = temp_storage[call.message.chat.id]['token']
                is_admin = get_permissions_by_token(user_token)
                keyboard = get_keyboard(is_admin)

                submit_gotocoins(user_token, id, money, comment)

                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=emoji.emojize(':thumbsup: GT начислены. Спасибо!', use_aliases=True))
                try:
                    student_id = find_telegram_by_id(id)
                    if student_id:
                        bot.send_message(student_id, emoji.emojize(':metal: Вам начислено {} GT за "{}".'.format(money, comment), use_aliases=True))
                except:
                    pass
                answer = bot.send_message(call.message.chat.id, "Что дальше?", reply_markup=keyboard)
                temp_storage[call.message.chat.id]['comment'] = {}
                bot.register_next_step_handler(answer, process_command)
            elif call.data == "no":
                user_token = temp_storage[call.message.chat.id]['token']
                is_admin = get_permissions_by_token(user_token)
                keyboard = get_keyboard(is_admin)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text=emoji.emojize(':confused: Нет, так нет. Отменяем.', use_aliases=True))
                answer = bot.send_message(call.message.chat.id, "Что дальше?", reply_markup=keyboard)
                temp_storage[call.message.chat.id]['comment'] = {}
                bot.register_next_step_handler(answer, process_command)
            else:
                raise Exception("unknown command")
        except Exception as e:
            print(e)
            answer = bot.send_message(call.message.chat.id, text='Что-то пошло не так :(')
            bot.register_next_step_handler(answer, process_command)

while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(e)
        pass
    time.sleep(5)