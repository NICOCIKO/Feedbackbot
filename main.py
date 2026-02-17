import telebot
from telebot import types

TOKEN = "ТВОЙ_ТОКЕН_БОТА"
ADMIN_ID = 7924774037  # твой ID
bot = telebot.TeleBot(TOKEN)

# Для хранения анонимных сообщений
anonymous_messages = {}

@bot.message_handler(commands=['start'])
def start_handler(message):
    if message.from_user.id == ADMIN_ID:
        markup = types.InlineKeyboardMarkup()
        stats_btn = types.InlineKeyboardButton("📊 Статистика", callback_data="stats")
        users_btn = types.InlineKeyboardButton("👥 Пользователи", callback_data="users")
        markup.add(stats_btn)
        markup.add(users_btn)
        bot.send_message(message.chat.id, "Привет, админ! Выбери действие:", reply_markup=markup)
    else:
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("📩 Написать сообщение", callback_data="send_message")
        btn2 = types.InlineKeyboardButton("🕵️ Написать анонимно", callback_data="send_anonymous")
        markup.add(btn1)
        markup.add(btn2)
        bot.send_message(message.chat.id, "Привет! Выбери способ отправки сообщения:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.from_user.id != ADMIN_ID:
        if call.data == "send_message":
            msg = bot.send_message(call.from_user.id, "Введите сообщение:")
            bot.register_next_step_handler(msg, send_message)
        elif call.data == "send_anonymous":
            msg = bot.send_message(call.from_user.id, "Введите анонимное сообщение:")
            bot.register_next_step_handler(msg, send_anonymous)
    else:
        if call.data == "stats":
            bot.send_message(ADMIN_ID, "Всего пользователей: ...")  # сюда логику можно добавить
        elif call.data == "users":
            bot.send_message(ADMIN_ID, "Список пользователей: ...")  # сюда логику можно добавить

def send_message(message):
    text = message.text
    bot.send_message(ADMIN_ID, f"Сообщение от {message.from_user.username} (ID: {message.from_user.id}): {text}")
    bot.send_message(message.from_user.id, "✅ Сообщение отправлено!")

def send_anonymous(message):
    text = message.text
    anonymous_messages[message.from_user.id] = text
    bot.send_message(ADMIN_ID, f"Анонимное сообщение от {message.from_user.username} (ID: {message.from_user.id}): {text}")
    bot.send_message(message.from_user.id, "✅ Сообщение отправлено анонимно!")

# Просто запускаем polling, без remove_webhook
bot.infinity_polling(timeout=60)
