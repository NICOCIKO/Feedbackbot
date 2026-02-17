import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, InputMediaVideo

TOKEN = "8341977158:AAGB6u5WiQ0LHrrEigv5NdrlSxtR9m33gKo"
ADMIN_ID = 7924774037  # Ваш Telegram ID

bot = telebot.TeleBot(TOKEN)

# Словари для хранения временных данных
user_state = {}   # что пользователь выбрал
messages_db = []  # все сообщения пользователей {user_id, username, content, type}

# --- Меню пользователей ---
def user_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("✉️ Написать анонимно", callback_data="user_anon"),
        InlineKeyboardButton("💬 Написать", callback_data="user_normal")
    )
    return markup

# --- Меню админа ---
def admin_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        InlineKeyboardButton("👥 Список пользователей", callback_data="admin_users")
    )
    return markup

# --- Отмена ---
def cancel_button():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("❌ Отмена", callback_data="cancel")
    )
    return markup

# --- Приветствие ---
@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(ADMIN_ID, "Привет, админ! Выбери действие:", reply_markup=admin_menu())
    else:
        bot.send_message(message.chat.id, "Привет! Я помогу тебе отправить сообщения @ne_nico.\nВыбери действие:", reply_markup=user_menu())

# --- Обработка нажатий инлайн кнопок ---
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id

    # --- Отмена ---
    if call.data == "cancel":
        try:
            bot.delete_message(user_id, call.message.message_id)
        except: pass
        if user_id == ADMIN_ID:
            bot.send_message(ADMIN_ID, "Выбери действие:", reply_markup=admin_menu())
        else:
            bot.send_message(user_id, "Выбери действие:", reply_markup=user_menu())
        user_state.pop(user_id, None)
        return

    # --- Меню пользователя ---
    if call.data in ["user_anon", "user_normal"]:
        user_state[user_id] = call.data
        try:
            bot.delete_message(user_id, call.message.message_id)
        except: pass
        bot.send_message(user_id, "Отправьте сообщение или медиа. Оно будет анонимным для других пользователей.", reply_markup=cancel_button())
        return

    # --- Меню админа ---
    if user_id == ADMIN_ID:
        if call.data == "admin_stats":
            bot.send_message(ADMIN_ID, f"Всего сообщений: {len(messages_db)}", reply_markup=admin_menu())
        elif call.data == "admin_users":
            if messages_db:
                users_list = "\n".join([f"{m['username']} ({m['user_id']})" for m in messages_db])
                bot.send_message(ADMIN_ID, f"Пользователи, кто писал:\n{users_list}", reply_markup=admin_menu())
            else:
                bot.send_message(ADMIN_ID, "Пока нет пользователей.", reply_markup=admin_menu())
        elif call.data.startswith("reply_"):
            target_id = int(call.data.split("_")[1])
            user_state[ADMIN_ID] = f"reply_{target_id}"
            bot.send_message(ADMIN_ID, "Напиши ответ пользователю:", reply_markup=cancel_button())
        return

# --- Обработка сообщений ---
@bot.message_handler(func=lambda m: True, content_types=['text', 'photo', 'video', 'document', 'audio'])
def handle_message(message):
    user_id = message.from_user.id

    # --- Админ отвечает ---
    if user_id == ADMIN_ID and user_id in user_state and str(user_state[user_id]).startswith("reply_"):
        target_id = int(str(user_state[user_id]).split("_")[1])
        try:
            bot.send_message(target_id, f"Сообщение от администратора:\n{message.text}")
        except:
            bot.send_message(ADMIN_ID, "Не удалось отправить сообщение пользователю.")
        bot.send_message(ADMIN_ID, "Ответ отправлен.", reply_markup=admin_menu())
        user_state.pop(user_id, None)
        return

    # --- Пользователь отправляет ---
    if user_id in user_state:
        data_type = user_state[user_id]
        content = None
        if message.content_type == 'text':
            content = message.text
        elif message.content_type in ['photo', 'video', 'document', 'audio']:
            content = message.file_id  # сохраняем id файла
        messages_db.append({
            'user_id': user_id,
            'username': message.from_user.username,
            'content': content,
            'type': message.content_type,
            'anonymous': data_type=="user_anon"
        })
        bot.send_message(user_id, "Сообщение отправлено!", reply_markup=user_menu())
        # Уведомление админу
        try:
            bot.send_message(ADMIN_ID,
                             f"Новое сообщение от {message.from_user.username} ({user_id}):\n{content}",
                             reply_markup=InlineKeyboardMarkup().add(
                                 InlineKeyboardButton("💬 Ответить", callback_data=f"reply_{user_id}")
                             ))
        except: pass
        user_state.pop(user_id, None)
        return

bot.infinity_polling()
