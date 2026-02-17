from telebot import TeleBot, types

bot = TeleBot("YOUR_BOT_TOKEN")

ADMIN_ID = 123456789  # твой Telegram ID

# Хранилища
user_state = {}       # user_id: состояние (обычное/аноним)
user_messages = {}    # user_id: список сообщений
pending_reply = {}    # admin_msg_id: user_id

# --- Клавиатура пользователя ---
def main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("✉️ Написать", callback_data="write"),
        types.InlineKeyboardButton("🕵️ Написать анонимно", callback_data="write_anonymous")
    )
    return markup

def cancel_button():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("❌ Отмена", callback_data="cancel"))
    return markup

# --- Кнопки для админа ---
def admin_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="stats"),
        types.InlineKeyboardButton("👥 Пользователи", callback_data="users")
    )
    return markup

# --- Кнопка ответить пользователю ---
def reply_button(admin_msg_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💬 Ответить", callback_data=f"reply_{admin_msg_id}"))
    return markup

# --- Старт ---
@bot.message_handler(commands=["start"])
def start(msg):
    if msg.from_user.id == ADMIN_ID:
        bot.send_message(msg.chat.id, "Привет, админ! Выбери действие:", reply_markup=admin_keyboard())
    else:
        bot.send_message(msg.chat.id, "Привет! Я помогу отправить сообщения/медиа или анонимку @ne_nico. Выбери действие:", reply_markup=main_keyboard())

# --- Обработка кнопок ---
@bot.callback_query_handler(func=lambda c: True)
def callback_handler(call):
    user_id = call.from_user.id
    data = call.data

    if data == "write":
        user_state[user_id] = "normal"
        bot.send_message(user_id, "Отправьте сообщение или медиа.", reply_markup=cancel_button())
        bot.delete_message(user_id, call.message.message_id)

    elif data == "write_anonymous":
        user_state[user_id] = "anonymous"
        bot.send_message(user_id, "Отправьте сообщение или медиа. Оно будет анонимным.", reply_markup=cancel_button())
        bot.delete_message(user_id, call.message.message_id)

    elif data == "cancel":
        bot.delete_message(user_id, call.message.message_id)
        bot.send_message(user_id, "Выберите действие:", reply_markup=main_keyboard())

    elif data.startswith("reply_"):
        admin_msg_id = int(data.split("_")[1])
        target_user = pending_reply.get(admin_msg_id)
        if target_user:
            user_state[target_user] = f"reply_{admin_msg_id}"
            bot.send_message(user_id, "Напишите ответ:", reply_markup=cancel_button())

    elif data == "stats":
        total_users = len(user_messages)
        bot.send_message(user_id, f"Всего пользователей: {total_users}")

    elif data == "users":
        if user_messages:
            text = "Список пользователей:\n" + "\n".join([f"{uid} | {uname}" for uid, uname in user_messages.items()])
        else:
            text = "Пользователи отсутствуют."
        bot.send_message(user_id, text)

# --- Приём сообщений ---
@bot.message_handler(content_types=["text", "photo", "video", "document", "sticker"])
def handle_message(msg):
    user_id = msg.from_user.id
    state = user_state.get(user_id)

    if state is None:
        bot.send_message(user_id, "Выберите действие:", reply_markup=main_keyboard())
        return

    # Сохраняем пользователя
    if user_id not in user_messages:
        user_messages[user_id] = msg.from_user.username or msg.from_user.first_name

    # Сообщение для админа
    if state == "normal" or state == "anonymous":
        text = ""
        if state == "normal":
            text += f"От {msg.from_user.username or msg.from_user.first_name} (ID: {user_id}):\n"
        text += msg.text or "<медиа сообщение>"
        sent = bot.send_message(ADMIN_ID, text, reply_markup=reply_button(msg.message_id))
        pending_reply[sent.message_id] = user_id
        bot.send_message(user_id, "Сообщение отправлено.", reply_markup=main_keyboard())

    elif state.startswith("reply_"):
        # Админ ответил пользователю
        reply_id = int(state.split("_")[1])
        target_user = pending_reply.get(reply_id)
        if target_user:
            bot.forward_message(target_user, msg.chat.id, msg.message_id)
            bot.send_message(target_user, "💬 Ответ от администратора", reply_markup=reply_button(msg.message_id))
            bot.send_message(msg.chat.id, "Ответ отправлен.", reply_markup=admin_keyboard())

    user_state[user_id] = None

bot.infinity_polling()
