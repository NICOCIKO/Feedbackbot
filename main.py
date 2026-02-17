import os
import telebot
from telebot import types

# ⚡ Токен бота
TOKEN = os.getenv("TOKEN")  # или вставь прямо "ВАШ_ТОКЕН"

# Список админов (Telegram ID)
ADMINS = [7924774037]  # добавь всех админов сюда

bot = telebot.TeleBot(TOKEN)

# Словарь для хранения состояния ответов
reply_to_user = {}

# ================= START =================
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Привет! Отправь мне сообщение, и оно придёт админам анонимно 🙂"
    )

# ================= RECEIVE MESSAGE =================
@bot.message_handler(func=lambda m: True)
def receive_message(message):
    sender = message.from_user

    # Кнопка для ответа для каждого админа
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("Ответить", callback_data=f"reply_{sender.id}")
    markup.add(btn)

    # Отправляем всем админам с раскрытием отправителя
    for admin in ADMINS:
        bot.send_message(
            admin,
            f"📩 Новое сообщение\n\n"
            f"Отправитель:\n"
            f"ID: {sender.id}\n"
            f"Username: @{sender.username if sender.username else 'нет'}\n"
            f"Имя: {sender.first_name}\n\n"
            f"Текст:\n{message.text}",
            reply_markup=markup
        )

    # Пользователю видим только, что сообщение отправлено
    bot.send_message(message.chat.id, "✅ Сообщение отправлено анонимно!")

# ================= REPLY BUTTON =================
@bot.callback_query_handler(func=lambda call: call.data.startswith("reply_"))
def reply_callback(call):
    sender_id = call.data.split("_")[1]
    reply_to_user[call.from_user.id] = sender_id
    bot.send_message(call.from_user.id, "✍️ Напиши ответ пользователю:")
    bot.answer_callback_query(call.id)

# ================= SEND REPLY =================
@bot.message_handler(func=lambda m: m.from_user.id in reply_to_user)
def send_reply(message):
    target_id = reply_to_user.pop(message.from_user.id)

    bot.send_message(
        target_id,
        f"📩 Админ ответил:\n\n{message.text}"
    )

    bot.send_message(message.chat.id, "✅ Ответ отправлен пользователю!")

# ================= RUN =================
print("Мини-бот с анонимными сообщениями для нескольких админов запущен...")
bot.infinity_polling()