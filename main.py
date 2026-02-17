import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ===== Настройки =====
BOT_TOKEN = "8341977158:AAGB6u5WiQ0LHrrEigv5NdrlSxtR9m33gKo"
ADMIN_ID = 7924774037  # Ваш ID, вы админ
bot = telebot.TeleBot(BOT_TOKEN)

# Словари для хранения состояния пользователей
user_states = {}  # user_id: "sending_anonymous"/"sending_normal"
messages_for_admin = {}  # user_id: [message_ids]

# ===== Кнопки =====
def user_menu():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🕵Написать анонимно", callback_data="anon"),
        InlineKeyboardButton("💬 Написать", callback_data="normal")
    )
    return markup

def cancel_button():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("❌ Отмена", callback_data="cancel"))
    return markup

def admin_menu():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("📊 Статистика", callback_data="stats"),
        InlineKeyboardButton("👥 Пользователи", callback_data="users")
    )
    return markup

def admin_reply_markup(user_id):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("💬 Ответить", callback_data=f"reply_{user_id}"))
    return markup

# ===== Старт =====
@bot.message_handler(commands=["start"])
def start_handler(message):
    user_id = message.from_user.id
    bot.send_message(
        user_id,
        f"Привет, {message.from_user.first_name}! 👋\n"
        "Я помогу тебе отправлять сообщения или анонимки @ne_nico",
        reply_markup=user_menu()
    )

# ===== Обработка выбора пользователя =====
@bot.callback_query_handler(func=lambda c: True)
def callback_handler(call):
    user_id = call.from_user.id
    if call.data == "anon":
        user_states[user_id] = "sending_anonymous"
        bot.delete_message(user_id, call.message.message_id)
        bot.send_message(user_id, "Отправьте сообщение или медиа. Оно будет анонимным.", reply_markup=cancel_button())
    elif call.data == "normal":
        user_states[user_id] = "sending_normal"
        bot.delete_message(user_id, call.message.message_id)
        bot.send_message(user_id, "Отправьте сообщение или медиа. Оно будет от вашего имени.", reply_markup=cancel_button())
    elif call.data == "cancel":
        user_states.pop(user_id, None)
        bot.delete_message(user_id, call.message.message_id)
        bot.send_message(user_id, "Выберите действие:", reply_markup=user_menu())
    elif call.data.startswith("reply_"):
        target_id = int(call.data.split("_")[1])
        bot.answer_callback_query(call.id, "Напиши ответ этому пользователю:")
        bot.register_next_step_handler_by_chat_id(ADMIN_ID, lambda msg: send_admin_response(target_id, msg))

# ===== Отправка сообщения админом =====
def send_admin_response(user_id, msg):
    bot.send_message(user_id, f"💬 Ответ от администратора:\n{msg.text}")
    bot.send_message(ADMIN_ID, "Ответ отправлен.", reply_markup=admin_menu())

# ===== Получение сообщений от пользователей =====
@bot.message_handler(content_types=["text", "photo", "video", "voice", "document", "sticker"])
def handle_user_message(message):
    user_id = message.from_user.id
    state = user_states.get(user_id)
    if not state:
        bot.send_message(user_id, "Выберите действие:", reply_markup=user_menu())
        return

    # Формируем сообщение для админа
    username = message.from_user.username or "NoUsername"
    if state == "sending_anonymous":
        text_for_admin = f"💌 Анонимное сообщение от @{username} ({user_id})"
        if message.content_type == "text":
            text_for_admin += f":\n{message.text}"
    else:  # обычное сообщение
        text_for_admin = f"📨 Сообщение от @{username} ({user_id})"
        if message.content_type == "text":
            text_for_admin += f":\n{message.text}"

    # Отправляем администратору
    sent = bot.send_message(ADMIN_ID, text_for_admin, reply_markup=admin_reply_markup(user_id))
    messages_for_admin.setdefault(user_id, []).append(sent.message_id)

    # Подтверждаем пользователю
    bot.send_message(user_id, "✅ Ваше сообщение отправлено!", reply_markup=user_menu())
    user_states.pop(user_id, None)

# ===== Запуск =====
bot.infinity_polling()
