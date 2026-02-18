from telebot import TeleBot, types

# ==== Настройки бота ====
TOKEN = "8341977158:AAGB6u5WiQ0LHrrEigv5NdrlSxtR9m33gKo"
ADMIN_ID = 7924774037

bot = TeleBot(TOKEN)

# ==== Хранилище состояния ====
user_language = {}
user_state = {}  # {'last_message_id': int, 'mode': str}
pending_replies = {}  # {admin_msg_id: user_id}

# ==== Сообщения ====
messages = {
    "start": {"ru": "Привет! Выбери язык 🌐", "en": "Hello! Choose your language 🌐"},
    "action": {"ru": "Выберите действие ✉️", "en": "Choose an action ✉️"},
    "message_sent": {"ru": "Сообщение отправлено ✅", "en": "Message sent ✅"},
    "anonymous_note": {"ru": "Отправьте сообщение или медиа. Оно будет анонимным 👻",
                       "en": "Send a message or media. It will be anonymous 👻"},
    "normal_note": {"ru": "Отправьте сообщение или медиа ✉️",
                    "en": "Send a message or media ✉️"}
}

# ==== Кнопки ====
def language_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        types.InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")
    )
    return kb

def action_keyboard(lang):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("✉️ Написать сообщение" if lang=="ru" else "✉️ Write message", callback_data="normal"),
        types.InlineKeyboardButton("👻 Анонимно" if lang=="ru" else "👻 Anonymous", callback_data="anonymous")
    )
    return kb

def cancel_keyboard(lang):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("❌ Отмена" if lang=="ru" else "❌ Cancel", callback_data="cancel"))
    return kb

def reply_keyboard(admin_msg_id):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("💬 Ответить", callback_data=f"reply_{admin_msg_id}"))
    return kb

def user_reply_keyboard(chat_id):
    lang = user_language.get(chat_id, "ru")
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("✉️ Написать сообщение" if lang=="ru" else "✉️ Write message", callback_data="normal"),
        types.InlineKeyboardButton("👻 Анонимно" if lang=="ru" else "👻 Anonymous", callback_data="anonymous")
    )
    return kb

# ==== Старт и выбор языка ====
@bot.message_handler(commands=["start"])
def start(msg):
    sent = bot.send_message(msg.chat.id, messages["start"]["ru"], reply_markup=language_keyboard())
    user_state[msg.chat.id] = {"last_message_id": sent.message_id}

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id

    # Выбор языка
    if call.data.startswith("lang_"):
        lang = call.data.split("_")[1]
        user_language[chat_id] = lang
        bot.delete_message(chat_id, call.message.message_id)
        sent = bot.send_message(chat_id, messages["action"][lang], reply_markup=action_keyboard(lang))
        user_state[chat_id]["last_message_id"] = sent.message_id

    # Действия
    elif call.data in ["normal", "anonymous"]:
        lang = user_language.get(chat_id, "ru")
        user_state[chat_id]["mode"] = call.data
        bot.delete_message(chat_id, call.message.message_id)
        note_msg = messages["normal_note"][lang] if call.data=="normal" else messages["anonymous_note"][lang]
        sent = bot.send_message(chat_id, note_msg, reply_markup=cancel_keyboard(lang))
        user_state[chat_id]["last_message_id"] = sent.message_id

    # Отмена
    elif call.data=="cancel":
        lang = user_language.get(chat_id, "ru")
        bot.delete_message(chat_id, user_state[chat_id]["last_message_id"])
        sent = bot.send_message(chat_id, messages["action"][lang], reply_markup=action_keyboard(lang))
        user_state[chat_id]["last_message_id"] = sent.message_id
        user_state[chat_id]["mode"] = None

    # Ответ админа
    elif call.data.startswith("reply_"):
        admin_msg_id = int(call.data.split("_")[1])
        target_user = pending_replies.get(admin_msg_id)
        if target_user:
            sent = bot.send_message(ADMIN_ID, "Напишите ответ пользователю ✉️")
            user_state[ADMIN_ID] = {"reply_to": target_user, "last_message_id": sent.message_id}

# ==== Получение сообщений от пользователей ====
@bot.message_handler(content_types=["text","photo","video","document","voice","audio"])
def receive(msg):
    chat_id = msg.chat.id
    lang = user_language.get(chat_id, "ru")

    # Админ пишет ответ пользователю
    if chat_id==ADMIN_ID and user_state.get(chat_id, {}).get("reply_to"):
        target_user = user_state[chat_id]["reply_to"]
        # Отправляем сообщение пользователю
        if msg.content_type=="text":
            sent = bot.send_message(target_user, f"💬 Ответ от администратора:\n{msg.text}", reply_markup=user_reply_keyboard(target_user))
        else:
            bot.forward_message(target_user, chat_id, msg.message_id)
            bot.send_message(target_user, "💬 Ответ от администратора:", reply_markup=user_reply_keyboard(target_user))
        user_state[chat_id]["reply_to"] = None
        return

    # Пользователь отправляет сообщение
    mode = user_state.get(chat_id, {}).get("mode")
    if not mode:
        return
    # Удаляем инструкцию пользователю
    bot.delete_message(chat_id, user_state[chat_id]["last_message_id"])
    bot.send_message(chat_id, messages["message_sent"][lang], reply_markup=user_reply_keyboard(chat_id))

    # Отправляем админу
    if mode=="normal":
        fwd = bot.forward_message(ADMIN_ID, chat_id, msg.message_id)
        bot.send_message(ADMIN_ID, f"От: @{msg.from_user.username} ({chat_id})", reply_markup=reply_keyboard(fwd.message_id))
    else:
        if msg.content_type=="text":
            fwd = bot.send_message(ADMIN_ID, f"Анонимное сообщение от: @{msg.from_user.username} ({chat_id})\n\n{msg.text}", reply_markup=reply_keyboard(msg.message_id))
        else:
            fwd = bot.forward_message(ADMIN_ID, chat_id, msg.message_id)
            bot.send_message(ADMIN_ID, f"Анонимное сообщение от: @{msg.from_user.username} ({chat_id})", reply_markup=reply_keyboard(fwd.message_id))

    # Сбрасываем состояние
    user_state[chat_id]["last_message_id"] = None
    user_state[chat_id]["mode"] = None

# ==== Запуск ====
bot.infinity_polling()
