import telebot
from telebot import types

TOKEN = "8341977158:AAGB6u5WiQ0LHrrEigv5NdrlSxtR9m33gKo"
ADMIN_ID = 7924774037  # ваш ID
bot = telebot.TeleBot(TOKEN)

# Сохраняем пользователей
users = set()

# ====== КНОПКИ ДЛЯ ПОЛЬЗОВАТЕЛЯ ======
def get_user_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📩 Написать", callback_data="send_message"),
        types.InlineKeyboardButton("🕵️ Написать анонимно", callback_data="send_anonymous")
    )
    return markup

# ====== СТАРТ ======
@bot.message_handler(commands=["start"])
def start_handler(message):
    users.add(message.from_user.id)
    bot.send_message(
        message.chat.id,
        "Привет! Выберите действие:",
        reply_markup=get_user_markup()
    )

# ====== ОБРАБОТКА КНОПОК ======
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "send_message":
        bot.send_message(call.from_user.id, "Отправьте сообщение или медиа, я перешлю админу с вашим именем.")
        bot.register_next_step_handler_by_chat_id(call.from_user.id, forward_message, anonymous=False)
    elif call.data == "send_anonymous":
        bot.send_message(call.from_user.id, "Отправьте сообщение или медиа, оно будет анонимным.")
        bot.register_next_step_handler_by_chat_id(call.from_user.id, forward_message, anonymous=True)

# ====== ПЕРЕСЫЛКА СООБЩЕНИЙ ======
def forward_message(message, anonymous=False):
    if message.content_type == "text":
        text = message.text
        if anonymous:
            bot.send_message(ADMIN_ID, f"Анонимное сообщение:\n\n{text}")
        else:
            bot.send_message(ADMIN_ID, f"Сообщение от {message.from_user.full_name}:\n\n{text}")
    else:
        # Пересылаем медиа
        bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
        if not anonymous:
            bot.send_message(ADMIN_ID, f"От {message.from_user.full_name}")

    bot.send_message(message.chat.id, "✅ Ваше сообщение отправлено!")

bot.infinity_polling()
