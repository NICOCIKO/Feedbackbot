import os
import telebot
from telebot import types

TOKEN = os.getenv("TOKEN")  # или вставь токен напрямую
ADMIN_ID = 7924774037

bot = telebot.TeleBot(TOKEN)

waiting_for_message = {}  # {user_id: "normal"/"anonymous"}
users = {}  # {user_id: username}
stats = {"normal": 0, "anonymous": 0}

# ================= START =================
@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    username = message.from_user.username or "нет"
    users[user_id] = username

    if user_id == ADMIN_ID:
        # Кнопки для админа
        markup = types.InlineKeyboardMarkup()
        btn_stats = types.InlineKeyboardButton("📊 Статистика", callback_data="stats")
        btn_users = types.InlineKeyboardButton("👥 Пользователи", callback_data="users")
        markup.add([btn_stats])
        markup.add([btn_users])
        bot.send_message(user_id, "Привет, админ! Выбери действие:", reply_markup=markup)
    else:
        # Кнопки для обычного пользователя
        markup = types.InlineKeyboardMarkup()
        btn_msg = types.InlineKeyboardButton("📩 Написать сообщение", callback_data="send_message")
        btn_anon = types.InlineKeyboardButton("🕵️ Написать анонимно", callback_data="send_anonymous")
        markup.add([btn_msg])
        markup.add([btn_anon])
        bot.send_message(user_id, "Привет! Выбери способ отправки сообщения:", reply_markup=markup)

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
    elif call.data == "stats" and user_id == ADMIN_ID:
        text = f"📊 Статистика сообщений:\n\n" \
               f"Обычные: {stats['normal']}\n" \
               f"Анонимные: {stats['anonymous']}"
        bot.send_message(user_id, text)
    elif call.data == "users" and user_id == ADMIN_ID:
        if users:
            text = "👥 Пользователи:\n\n" + "\n".join([f"{uid} — @{uname}" for uid, uname in users.items()])
        else:
            text = "Нет пользователей."
        bot.send_message(user_id, text)
    bot.answer_callback_query(call.id)

# ================= RECEIVE MESSAGE =================
@bot.message_handler(func=lambda m: m.from_user.id in waiting_for_message)
def receive_message(message):
    mode = waiting_for_message.pop(message.from_user.id)
    sender = message.from_user
    is_anon = mode == "anonymous"

    # Считаем статистику
    stats[mode] += 1

    # Сохраняем пользователя
    users[sender.id] = sender.username or "нет"

    # Отправляем админу
    bot.send_message(
        ADMIN_ID,
        f"{'🕵️ Анонимное сообщение' if is_anon else '📩 Обычное сообщение'}\n\n"
        f"Отправитель:\nID: {sender.id}\nUsername: @{sender.username if sender.username else 'нет'}\n\n"
        f"Текст:\n{message.text}"
    )

    # Сообщение пользователю
    bot.send_message(
        sender.id,
        "✅ Сообщение отправлено анонимно!" if is_anon else "✅ Сообщение отправлено!"
    )

# ================= RUN =================
bot.remove_webhook()
bot.infinity_polling()
