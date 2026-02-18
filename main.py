import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8341977158:AAGB6u5WiQ0LHrrEigv5NdrlSxtR9m33gKo"
ADMIN_ID = 7924774037  # Ваш Telegram ID

bot = telebot.TeleBot(TOKEN)

users = {}

# Главное меню
def main_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("Написать сообщение", callback_data="write"),
        InlineKeyboardButton("Отправить анонимно", callback_data="anon")
    )
    return markup

# Старт
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    users[user_id] = message.from_user.username or "Без username"
    bot.send_message(user_id, "Выберите действие:", reply_markup=main_menu())

# Обработка кнопок
@bot.callback_query_handler(func=lambda c: True)
def callback_handler(call):
    user_id = call.from_user.id

    # Удаляем старое сообщение с кнопками
    bot.delete_message(user_id, call.message.message_id)

    if call.data == "write":
        msg = bot.send_message(user_id, "Введите сообщение:")
        bot.register_next_step_handler(msg, process_message, False, msg.message_id)

    elif call.data == "anon":
        msg = bot.send_message(user_id, "Введите анонимное сообщение:")
        bot.register_next_step_handler(msg, process_message, True, msg.message_id)

# Обработка сообщения
def process_message(message, is_anon, prompt_id):
    user_id = message.from_user.id
    username = users.get(user_id, "Без username")

    # Удаляем сообщение "Введите сообщение"
    bot.delete_message(user_id, prompt_id)

    header = (
        f"📩 Анонимное сообщение\nОт: @{username}\nID: {user_id}\n\n"
        if is_anon else
        f"📩 Сообщение\nОт: @{username}\nID: {user_id}\n\n"
    )

    # Текст
    if message.content_type == "text":
        bot.send_message(ADMIN_ID, header + message.text)

    # Фото
    elif message.content_type == "photo":
        bot.send_photo(
            ADMIN_ID,
            message.photo[-1].file_id,
            caption=header
        )

    # Видео
    elif message.content_type == "video":
        bot.send_video(
            ADMIN_ID,
            message.video.file_id,
            caption=header
        )

    # Документ
    elif message.content_type == "document":
        bot.send_document(
            ADMIN_ID,
            message.document.file_id,
            caption=header
        )

    # Аудио
    elif message.content_type == "audio":
        bot.send_audio(
            ADMIN_ID,
            message.audio.file_id,
            caption=header
        )

    # Подтверждение пользователю
    bot.send_message(user_id, "✅ Сообщение отправлено!", reply_markup=main_menu())

bot.infinity_polling()
