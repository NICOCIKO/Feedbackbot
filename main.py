import telebot
from telebot import types

# ====== Настройки ======
TOKEN = "8518294250:AAFvzz5OQKsx174GRWkb1NV0ZnKdBkvdZS8"
ADMIN_ID = 7924774037
bot = telebot.TeleBot(TOKEN)

# ====== Хранилище ======
users_language = {}  # user_id: "ru" или "en"
pending_messages = {}  # user_id: {"type": "anon"/"normal", "message_id": id}
message_to_admin = {}  # admin_msg_id: {"user_id": id, "type": "anon"/"normal"}

# ====== Тексты ======
texts = {
    "ru": {
        "start": "🌍 Выберите язык / Select language",
        "choose_action": "💌 Выберите действие:",
        "send_message": "💬 Написать сообщение",
        "send_anonymous": "🤫 Анонимно",
        "send_prompt": "✉️ Отправьте сообщение или медиа.",
        "send_anonymous_prompt": "✉️ Отправьте сообщение или медиа. Оно будет анонимным.",
        "cancel": "❌ Отмена",
        "sent": "✅ Сообщение отправлено!",
        "reply": "💬 Ответить"
    },
    "en": {
        "start": "🌍 Choose language / Выберите язык",
        "choose_action": "💌 Choose action:",
        "send_message": "💬 Write message",
        "send_anonymous": "🤫 Anonymous",
        "send_prompt": "✉️ Send a message or media.",
        "send_anonymous_prompt": "✉️ Send a message or media. It will be anonymous.",
        "cancel": "❌ Cancel",
        "sent": "✅ Message sent!",
        "reply": "💬 Reply"
    }
}

# ====== Старт ======
@bot.message_handler(commands=["start"])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🇷🇺", callback_data="lang_ru"),
        types.InlineKeyboardButton("🇬🇧", callback_data="lang_en")
    )
    msg = bot.send_message(message.chat.id, "🌍 Выберите язык / Select language", reply_markup=markup)

# ====== Callback ======
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    user_id = call.from_user.id

    # ====== Выбор языка ======
    if call.data.startswith("lang_"):
        lang = call.data.split("_")[1]
        users_language[user_id] = lang
        bot.delete_message(user_id, call.message.message_id)  # удалить выбор языка

        send_choose_action(user_id)

    # ====== Действия пользователя ======
    elif call.data == "write":
        lang = users_language.get(user_id, "ru")
        msg = bot.send_message(user_id, texts[lang]["send_prompt"], reply_markup=cancel_markup(lang))
        pending_messages[user_id] = {"type": "normal", "message_id": msg.message_id}

    elif call.data == "anon":
        lang = users_language.get(user_id, "ru")
        msg = bot.send_message(user_id, texts[lang]["send_anonymous_prompt"], reply_markup=cancel_markup(lang))
        pending_messages[user_id] = {"type": "anon", "message_id": msg.message_id}

    elif call.data == "cancel":
        lang = users_language.get(user_id, "ru")
        # удалить предыдущие сообщения
        if user_id in pending_messages:
            try:
                bot.delete_message(user_id, pending_messages[user_id]["message_id"])
            except: pass
            pending_messages.pop(user_id)
        send_choose_action(user_id)

    # ====== Админ ответ ======
    elif call.data.startswith("reply_"):
        original_user_id = int(call.data.split("_")[1])
        lang = users_language.get(original_user_id, "ru")
        msg = bot.send_message(ADMIN_ID, f"✉️ Ответ пользователю {original_user_id}", reply_markup=cancel_markup(lang))
        pending_messages[ADMIN_ID] = {"type": "reply", "user_id": original_user_id, "message_id": msg.message_id}

# ====== Отправка сообщения пользователю ======
@bot.message_handler(content_types=["text", "photo", "video", "voice", "document"])
def handle_message(message):
    user_id = message.from_user.id
    lang = users_language.get(user_id, "ru")

    # ====== Пользователь отправляет сообщение ======
    if user_id in pending_messages:
        data = pending_messages.pop(user_id)
        # удаляем сообщение с инструкцией
        try:
            bot.delete_message(user_id, data["message_id"])
        except: pass

        # отправляем админу
        if data["type"] == "anon":
            text_to_admin = f"✉️ Анонимное сообщение\nID: {user_id}\nUsername: @{message.from_user.username if message.from_user.username else 'none'}"
        else:
            text_to_admin = f"✉️ Сообщение от @{message.from_user.username if message.from_user.username else 'none'} (ID: {user_id})"

        # пересылаем текст/медиа
        if message.content_type == "text":
            msg = bot.send_message(ADMIN_ID, text_to_admin + "\n\n" + message.text, reply_markup=reply_markup(user_id))
        elif message.content_type == "photo":
            msg = bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=text_to_admin, reply_markup=reply_markup(user_id))
        elif message.content_type == "video":
            msg = bot.send_video(ADMIN_ID, message.video.file_id, caption=text_to_admin, reply_markup=reply_markup(user_id))
        elif message.content_type == "voice":
            msg = bot.send_voice(ADMIN_ID, message.voice.file_id, caption=text_to_admin, reply_markup=reply_markup(user_id))
        elif message.content_type == "document":
            msg = bot.send_document(ADMIN_ID, message.document.file_id, caption=text_to_admin, reply_markup=reply_markup(user_id))

        message_to_admin[msg.message_id] = {"user_id": user_id, "type": data["type"]}

        # уведомление пользователю
        bot.send_message(user_id, texts[lang]["sent"])
        send_choose_action(user_id)

    # ====== Админ отвечает ======
    elif user_id == ADMIN_ID and user_id in pending_messages:
        data = pending_messages.pop(user_id)
        target_user = data["user_id"]
        lang = users_language.get(target_user, "ru")

        # пересылаем обратно пользователю
        if message.content_type == "text":
            bot.send_message(target_user, f"💌 Ответ администратора:\n\n{message.text}", reply_markup=reply_markup(target_user))
        elif message.content_type == "photo":
            bot.send_photo(target_user, message.photo[-1].file_id, caption=f"💌 Ответ администратора", reply_markup=reply_markup(target_user))
        elif message.content_type == "video":
            bot.send_video(target_user, message.video.file_id, caption=f"💌 Ответ администратора", reply_markup=reply_markup(target_user))
        elif message.content_type == "voice":
            bot.send_voice(target_user, message.voice.file_id, caption=f"💌 Ответ администратора", reply_markup=reply_markup(target_user))
        elif message.content_type == "document":
            bot.send_document(target_user, message.document.file_id, caption=f"💌 Ответ администратора", reply_markup=reply_markup(target_user))

# ====== Кнопки ======
def send_choose_action(user_id):
    lang = users_language.get(user_id, "ru")
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(texts[lang]["send_message"], callback_data="write")
    )
    markup.add(
        types.InlineKeyboardButton(texts[lang]["send_anonymous"], callback_data="anon")
    )
    bot.send_message(user_id, texts[lang]["choose_action"], reply_markup=markup)

def cancel_markup(lang):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(texts[lang]["cancel"], callback_data="cancel"))
    return markup

def reply_markup(user_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(texts["ru"]["reply"], callback_data=f"reply_{user_id}"))
    return markup

# ====== Запуск ======
bot.infinity_polling()
