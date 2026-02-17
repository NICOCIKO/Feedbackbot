import os
import telebot
from telebot import types

TOKEN = os.getenv("TOKEN")  # или вставьте токен напрямую
ADMIN_ID = 7924774037

bot = telebot.TeleBot(TOKEN)

waiting_for_message = {}  # {user_id: "normal"/"anonymous"}
reply_to_user = {}        # {admin_id: (target_user_id, is_anonymous)}

# ================= START =================
@bot.message_handler(commands=['start'])
def start_handler(message):
    text = "Привет! Выбери способ отправки сообщения:"

    markup = types.InlineKeyboardMarkup()
    btn_msg = types.InlineKeyboardButton("📩 Написать сообщение", callback_data="send_message")
    btn_anon = types.InlineKeyboardButton("🕵️ Написать анонимно", callback_data="send_anonymous")
    markup.add([btn_msg])
    markup.add([btn_anon])

    bot.send_message(message.chat.id, text, reply_markup=markup)

# ================= CALLBACK =================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id

    if call.data == "send_message":
        waiting_for_message[user_id] = "normal"
        bot.send_message(user_id, "✍️ Напиши своё сообщение:")
    elif call.data == "send_anonymous":
        waiting_for_message[user_id] = "anonymous"
        bot.send_message(user_id, "✍️ Напиши анонимное сообщение:")
    elif call.data.startswith("reply_"):
        target_id, anon_flag = call.data.split("_")[1], call.data.split("_")[2] == "anon"
        reply_to_user[user_id] = (int(target_id), anon_flag)
        bot.send_message(user_id, "✍️ Напиши ответ пользователю:")
    bot.answer_callback_query(call.id)

# ================= RECEIVE MESSAGE =================
@bot.message_handler(func=lambda m: m.from_user.id in waiting_for_message)
def receive_message(message):
    mode = waiting_for_message.pop(message.from_user.id)
    sender = message.from_user
    is_anon = mode == "anonymous"

    # Кнопка ответа для админа
    markup = types.InlineKeyboardMarkup()
    reply_btn = types.InlineKeyboardButton(
        "Ответить", callback_data=f"reply_{sender.id}_{'anon' if is_anon else 'norm'}"
    )
    markup.add([reply_btn])

    # Отправляем админу
    bot.send_message(
        ADMIN_ID,
        f"{'🕵️ Анонимное сообщение' if is_anon else '📩 Обычное сообщение'}\n\n"
        f"Отправитель:\nID: {sender.id}\nUsername: @{sender.username if sender.username else 'нет'}\n\n"
        f"Текст:\n{message.text}",
        reply_markup=markup
    )

    # Уведомление пользователю
    bot.send_message(
        sender.id,
        "✅ Сообщение отправлено анонимно!" if is_anon else "✅ Сообщение отправлено!"
    )

# ================= SEND REPLY =================
@bot.message_handler(func=lambda m: m.from_user.id in reply_to_user)
def send_reply(message):
    target_id, is_anon = reply_to_user.pop(message.from_user.id)
    # Админ отвечает пользователю
    bot.send_message(target_id, f"📩 Админ ответил:\n\n{message.text}")
    bot.send_message(message.chat.id, "✅ Ответ отправлен пользователю!")

# ================= RUN =================
bot.remove_webhook()
bot.infinity_polling()
