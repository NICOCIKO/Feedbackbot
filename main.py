import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from collections import defaultdict

TOKEN = "8341977158:AAGB6u5WiQ0LHrrEigv5NdrlSxtR9m33gKo"
ADMIN_ID = 7924774037  # твой Telegram ID
bot = telebot.TeleBot(TOKEN)

# Хранилище
users = {}  # user_id -> username
anon_messages = {}  # msg_id -> {"user_id": , "username": , "content": , "type": }

# Клавиатуры
def get_main_markup():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("✉️ Отправить сообщение", callback_data="send_normal"),
        InlineKeyboardButton("🕵️ Отправить анонимно", callback_data="send_anon")
    )
    return markup

def get_cancel_markup():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("❌ Отмена", callback_data="cancel")
    )
    return markup

# Старт
@bot.message_handler(commands=["start"])
def start_handler(message):
    users[message.from_user.id] = message.from_user.username
    bot.send_message(
        message.chat.id,
        f"Привет, {message.from_user.first_name}! 👋\nВыберите действие:",
        reply_markup=get_main_markup()
    )

# Обработка инлайн кнопок
@bot.callback_query_handler(func=lambda c: True)
def callback_handler(call):
    user_id = call.from_user.id

    if call.data == "send_normal":
        msg = bot.send_message(user_id, "Отправьте сообщение или медиа:", reply_markup=get_cancel_markup())
        bot.register_next_step_handler(msg, handle_normal)

    elif call.data == "send_anon":
        msg = bot.send_message(user_id, "Отправьте сообщение или медиа. Оно будет анонимным:", reply_markup=get_cancel_markup())
        bot.register_next_step_handler(msg, handle_anon)

    elif call.data == "cancel":
        bot.delete_message(user_id, call.message.message_id)
        bot.send_message(user_id, "Выберите действие:", reply_markup=get_main_markup())

    elif call.data.startswith("reply_"):
        target_id = int(call.data.split("_")[1])
        msg = bot.send_message(user_id, f"Введите сообщение для @{users.get(target_id, 'пользователь')}:")
        bot.register_next_step_handler(msg, lambda m: send_reply(m, target_id))

    elif call.data == "users_list" and user_id == ADMIN_ID:
        text = "Список пользователей:\n" + "\n".join([f"@{u}" for u in users.values()]) if users else "Пользователей нет."
        bot.send_message(user_id, text)

    elif call.data == "stats" and user_id == ADMIN_ID:
        text = f"Всего пользователей: {len(users)}\nАнонимных сообщений: {len(anon_messages)}"
        bot.send_message(user_id, text)

# Обработка обычных сообщений и медиа для пользователя
@bot.message_handler(content_types=['text', 'photo', 'video', 'voice', 'document', 'audio'])
def handle_media(message):
    # Сохраняем юзера
    users[message.from_user.id] = message.from_user.username

    # Проверяем, есть ли текущий шаг с анонимкой
    if hasattr(message, 'next_step_handler') and message.next_step_handler.__name__ == "handle_anon":
        anon_messages[message.message_id] = {
            "user_id": message.from_user.id,
            "username": message.from_user.username,
            "content": message,
            "type": message.content_type
        }
        bot.send_message(message.chat.id, "Ваше анонимное сообщение отправлено ✅", reply_markup=get_main_markup())

        # Отправка админу
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("Ответить", callback_data=f"reply_{message.from_user.id}"))

        text_preview = message.text if message.content_type == "text" else f"{message.content_type} прислано"
        bot.send_message(
            ADMIN_ID,
            f"Анонимное сообщение от @{message.from_user.username} (ID: {message.from_user.id}):\n{text_preview}",
            reply_markup=markup
        )

    else:
        bot.send_message(message.chat.id, "Ваше сообщение отправлено ✅", reply_markup=get_main_markup())

# Обработка обычного текста для кнопок
def handle_normal(message):
    users[message.from_user.id] = message.from_user.username
    bot.send_message(message.chat.id, "Ваше сообщение отправлено ✅", reply_markup=get_main_markup())

def handle_anon(message):
    # просто передаём в общий handler
    handle_media(message)

def send_reply(message, target_user_id):
    bot.send_message(target_user_id, f"Сообщение от администратора:\n{message.text}")
    bot.send_message(ADMIN_ID, "Сообщение отправлено ✅", reply_markup=get_main_markup())

bot.infinity_polling()
