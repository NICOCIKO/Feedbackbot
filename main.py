import os
import telebot
from telebot import types

TOKEN = os.getenv("TOKEN")  # или вставь прямо токен
ADMIN_ID = 7924774037       # твой Telegram ID

bot = telebot.TeleBot(TOKEN)

# Состояние пользователей
user_state = {}
reply_to_user = {}

# ================= START =================
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("✉️ Написать сообщение", "🕵️ Написать анонимно")
    bot.send_message(message.chat.id, "Привет! Выбери способ отправки фидбека:", reply_markup=markup)

# ================= CHOICE =================
@bot.message_handler(func=lambda m: m.text in ["✉️ Написать сообщение", "🕵️ Написать анонимно"])
def choose_feedback(message):
    if message.text == "✉️ Написать сообщение":
        user_state[message.from_user.id] = "normal"
        bot.send_message(message.chat.id, "✍️ Напиши своё сообщение:")
    else:
        user_state[message.from_user.id] = "anonymous"
        bot.send_message(message.chat.id, "✍️ Напиши анонимное сообщение:")

# ================= RECEIVE FEEDBACK =================
@bot.message_handler(func=lambda m: m.from_user.id in user_state)
def receive_feedback(message):
    state = user_state.pop(message.from_user.id)
    sender = message.from_user

    # Кнопка для ответа админа
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("Ответить", callback_data=f"reply_{sender.id}")
    markup.add(btn)

    # Отправка админу с раскрытием отправителя
    bot.send_message(
        ADMIN_ID,
        f"📩 Новый фидбек ({'Анонимно' if state=='anonymous' else 'Обычное'}):\n\n"
        f"Отправитель:\n"
        f"ID: {sender.id}\n"
        f"Username: @{sender.username if sender.username else 'нет'}\n"
        f"Имя: {sender.first_name}\n\n"
        f"Текст:\n{message.text}",
        reply_markup=markup
    )

    bot.send_message(message.chat.id, "✅ Сообщение отправлено!")

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
print("Feedback бот запущен...")
bot.infinity_polling()
