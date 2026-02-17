import telebot
from telebot import types

TOKEN = "8341977158:AAGB6u5WiQ0LHrrEigv5NdrlSxtR9m33gKo"
ADMIN_ID = 7924774037  # твой Telegram ID

bot = telebot.TeleBot(TOKEN)
users = {}  # хранение выбора пользователя

# Клавиатура с действиями
def get_user_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📩 Написать", callback_data="write"))
    markup.add(types.InlineKeyboardButton("🕵️ Написать анонимно", callback_data="anonymous"))
    return markup

# Клавиатура с кнопкой отмены
def get_cancel_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("❌ Отмена", callback_data="cancel"))
    return markup

# /start
@bot.message_handler(commands=['start'])
def start_handler(message):
    if message.from_user.id == ADMIN_ID:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📊 Статистика", callback_data="stats"))
        markup.add(types.InlineKeyboardButton("👥 Пользователи", callback_data="users"))
        bot.send_message(message.chat.id, "Привет, админ! Выбери действие:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=get_user_markup())

# Кнопки
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    # Удаляем сообщение с кнопками
    bot.delete_message(chat_id, call.message.message_id)

    if user_id == ADMIN_ID:
        if call.data == "stats":
            bot.send_message(user_id, f"Всего пользователей: {len(users)}")
        elif call.data == "users":
            bot.send_message(user_id, "Список пользователей:\n" + "\n".join(str(uid) for uid in users.keys()))
    else:
        if call.data in ["write", "anonymous"]:
            users[user_id] = call.data  # сохраняем выбор пользователя
            bot.send_message(chat_id, "Отправьте ваше сообщение (текст или медиа):", reply_markup=get_cancel_markup())

        elif call.data == "cancel":
            # Если нажали отмену — показываем кнопки снова
            bot.send_message(chat_id, "Выберите действие:", reply_markup=get_user_markup())

# Сообщения пользователя
@bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'video', 'voice', 'document'])
def handle_user_message(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id in users:
        choice = users.pop(user_id)  # получаем выбор и убираем из словаря

        # Отправка админу
        if message.content_type == 'text':
            content = message.text
            admin_msg = f"{'Анонимное' if choice == 'anonymous' else 'Сообщение'}:\n{content}"
            if choice == "anonymous":
                admin_msg += f"\n\nЮзернейм: @{message.from_user.username if message.from_user.username else 'не указан'}\nID: {user_id}"
            bot.send_message(ADMIN_ID, admin_msg)

        elif message.content_type == 'photo':
            file_id = message.photo[-1].file_id
            caption = None if choice == "write" else f"Юзернейм: @{message.from_user.username if message.from_user.username else 'не указан'}\nID: {user_id}"
            bot.send_photo(ADMIN_ID, file_id, caption=caption)

        elif message.content_type == 'video':
            file_id = message.video.file_id
            caption = None if choice == "write" else f"Юзернейм: @{message.from_user.username if message.from_user.username else 'не указан'}\nID: {user_id}"
            bot.send_video(ADMIN_ID, file_id, caption=caption)

        elif message.content_type == 'voice':
            file_id = message.voice.file_id
            caption = None if choice == "write" else f"Юзернейм: @{message.from_user.username if message.from_user.username else 'не указан'}\nID: {user_id}"
            bot.send_voice(ADMIN_ID, file_id, caption=caption)

        elif message.content_type == 'document':
            file_id = message.document.file_id
            caption = None if choice == "write" else f"Юзернейм: @{message.from_user.username if message.from_user.username else 'не указан'}\nID: {user_id}"
            bot.send_document(ADMIN_ID, file_id, caption=caption)

        # Подтверждение пользователю
        bot.send_message(chat_id, "✅ Сообщение отправлено!")

        # Снова показать кнопки
        bot.send_message(chat_id, "Выберите действие:", reply_markup=get_user_markup())

bot.infinity_polling()
