import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, InputMediaVideo

TOKEN = "8341977158:AAGB6u5WiQ0LHrrEigv5NdrlSxtR9m33gKo"
ADMIN_ID = 7924774037  # Ваш Telegram ID
bot = telebot.TeleBot(TOKEN)

# Хранилище сообщений и пользователей
users = {}          # user_id: username
anon_messages = {}  # message_id: (user_id, content, media_type)

# Приветствие
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    users[user_id] = message.from_user.username or "Без имени"
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton("Отправить сообщение", callback_data="write"),
        InlineKeyboardButton("Отправить анонимно", callback_data="anon")
    )
    bot.send_message(user_id, f"Привет, {users[user_id]}! Я помогу тебе отправить сообщение @ne_nico", reply_markup=markup)

# Обработка нажатий кнопок
@bot.callback_query_handler(func=lambda c: True)
def callback_handler(call):
    user_id = call.from_user.id
    msg_id = call.message.message_id

    # Удаляем старое сообщение с кнопками
    bot.delete_message(user_id, msg_id)

    if call.data in ["write", "anon"]:
        anon = call.data == "anon"
        text = "Отправьте сообщение или медиа. Оно будет анонимным." if anon else "Отправьте сообщение или медиа."
        sent_msg = bot.send_message(user_id, text)
        bot.register_next_step_handler(sent_msg, handle_message, anon, sent_msg.message_id)

    elif call.data == "cancel":
        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        markup.add(
            InlineKeyboardButton("Отправить сообщение", callback_data="write"),
            InlineKeyboardButton("Отправить анонимно", callback_data="anon")
        )
        bot.send_message(user_id, "Выберите действие:", reply_markup=markup)

# Обработка текста и медиа
def handle_message(message, anon, prompt_id):
    user_id = message.from_user.id

    # Удаляем сообщение с инструкцией
    bot.delete_message(user_id, prompt_id)

    content = None
    media_type = None

    if message.content_type == "text":
        content = message.text
    elif message.content_type in ["photo", "video", "document", "audio"]:
        file_id = None
        if message.content_type == "photo":
            file_id = message.photo[-1].file_id
            media_type = "photo"
        elif message.content_type == "video":
            file_id = message.video.file_id
            media_type = "video"
        elif message.content_type == "document":
            file_id = message.document.file_id
            media_type = "document"
        elif message.content_type == "audio":
            file_id = message.audio.file_id
            media_type = "audio"
        content = file_id

    # Отправляем админу
    send_to_admin(user_id, content, media_type, anon)

    # Подтверждение для пользователя
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton("Отправить сообщение", callback_data="write"),
        InlineKeyboardButton("Отправить анонимно", callback_data="anon")
    )
    bot.send_message(user_id, "Сообщение отправлено! Выберите действие:", reply_markup=markup)

def send_to_admin(sender_id, content, media_type, anon):
    username = users.get(sender_id, "Без имени")
    header = f"Анонимное сообщение от @{username} (ID: {sender_id})" if anon else f"Сообщение от @{username} (ID: {sender_id})"

    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton("Ответить", callback_data=f"reply_{sender_id}")
    )

    if media_type == "photo":
        bot.send_photo(ADMIN_ID, content, caption=header, reply_markup=markup)
    elif media_type == "video":
        bot.send_video(ADMIN_ID, content, caption=header, reply_markup=markup)
    elif media_type == "document":
        bot.send_document(ADMIN_ID, content, caption=header, reply_markup=markup)
    elif media_type == "audio":
        bot.send_audio(ADMIN_ID, content, caption=header, reply_markup=markup)
    else:
        bot.send_message(ADMIN_ID, f"{header}:\n{content}", reply_markup=markup)

# Обработка ответа админа
@bot.callback_query_handler(func=lambda c: c.data.startswith("reply_"))
def reply_handler(call):
    target_id = int(call.data.split("_")[1])
    bot.delete_message(call.from_user.id, call.message.message_id)
    sent_msg = bot.send_message(ADMIN_ID, f"Введите ответ пользователю @{users.get(target_id,'Без имени')} (ID: {target_id})")
    bot.register_next_step_handler(sent_msg, send_reply_to_user, target_id)

def send_reply_to_user(message, target_id):
    if message.content_type == "text":
        bot.send_message(target_id, f"Ответ от администратора: {message.text}")
    elif message.content_type in ["photo", "video", "document", "audio"]:
        file_id = None
        media_type = message.content_type
        if media_type == "photo":
            file_id = message.photo[-1].file_id
            bot.send_photo(target_id, file_id, caption="Ответ от администратора")
        elif media_type == "video":
            file_id = message.video.file_id
            bot.send_video(target_id, file_id, caption="Ответ от администратора")
        elif media_type == "document":
            file_id = message.document.file_id
            bot.send_document(target_id, file_id, caption="Ответ от администратора")
        elif media_type == "audio":
            file_id = message.audio.file_id
            bot.send_audio(target_id, file_id, caption="Ответ от администратора")

bot.infinity_polling()
