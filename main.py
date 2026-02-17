import os
import telebot
from telebot import types

TOKEN = os.getenv("TOKEN")  # вставь токен
ADMIN_ID = 7924774037       # твой Telegram ID

bot = telebot.TeleBot(TOKEN)

# Состояние пользователей
user_state = {}
reply_to_user = {}

# ================= START =================
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✉️ Написать сообщение / Write a message", callback_data="normal"),
        types.InlineKeyboardButton("🕵️ Написать анонимно / Write anonymously", callback_data="anonymous")
    )
    bot.send_message(
        message.chat.id,
        "Привет! Выбери способ отправки сообщения:\n"
        "Hello! Choose how to send your feedback:",
        reply_markup=markup
    )

# ================= BUTTON CALLBACK =================
@bot.callback_query_handler(func=lambda call: call.data in ["normal", "anonymous"])
def choose_feedback(call):
    if call.data == "normal":
        user_state[call.from_user.id] = "normal"
        bot.send_message(call.from_user.id, "✍️ Напиши своё сообщение:\nWrite your message:")
    else:
        user_state[call.from_user.id] = "anonymous"
        bot.send_message(call.from_user.id, "✍️ Напиши анонимное сообщение:\nWrite your message anonymously:")
    bot.answer_callback_query(call.id)

# ================= RECEIVE MESSAGE =================
@bot.message_handler(func=lambda m: m.from_user.id in user_state)
def receive_feedback(message):
    state = user_state.pop(message.from_user.id)
    sender = message.from_user

    # Кнопка для ответа админа
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("Ответить / Reply", callback_data=f"reply_{sender.id}")
    markup.add(btn)

    # Отправка админу с раскрытием отправителя
    bot.send_message(
        ADMIN_ID,
        f"📩 Новый фидбек ({'Анонимно / Anonymous' if state=='anonymous' else 'Обычное / Normal'}):\n\n"
        f"Отправитель:\nID: {sender.id}\nUsername: @{sender.username if sender.username else 'нет / none'}\nИмя / Name: {sender.first_name}\n\n"
        f"Текст / Message:\n{message.text}",
        reply_markup=markup
    )

    bot.send_message(message.chat.id, "✅ Сообщение отправлено! / Message sent!")

# ================= REPLY BUTTON =================
@bot.callback_query_handler(func=lambda call: call.data.startswith("reply_"))
def reply_callback(call):
    sender_id = call.data.split("_")[1]
    reply_to_user[call.from_user.id] = sender_id
    bot.send_message(call.from_user.id, "✍️ Напиши ответ пользователю / Write your reply to the user:")
    bot.answer_callback_query(call.id)

# ================= SEND REPLY =================
@bot.message_handler(func=lambda m: m.from_user.id in reply_to_user)
def send_reply(message):
    target_id = reply_to_user.pop(message.from_user.id)

    bot.send_message(
        target_id,
        f"📩 Админ ответил / Admin replied:\n\n{message.text}"
    )

    bot.send_message(message.chat.id, "✅ Ответ отправлен пользователю / Reply sent!")

# ================= RUN =================
print("Feedback бот (двуязычный) запущен...")
bot.infinity_polling()
