from telebot import TeleBot, types

TOKEN = "8341977158:AAGB6u5WiQ0LHrrEigv5NdrlSxtR9m33gKo"
ADMIN_ID = 7924774037  # Ваш ID
bot = TeleBot(TOKEN)

users = {}  # Хранилище пользователей и состояний
pending_admin_reply = {}  # Для ответа админа

texts = {
    "ru": {
        "choose_lang": "Выберите язык 🇷🇺",
        "prompt_anonymous": "Отправьте сообщение или медиа. Оно будет анонимным 👤",
        "prompt_normal": "Отправьте сообщение или медиа ✉️",
        "sent": "Ваше сообщение отправлено ✅",
        "action": "Выберите действие:",
        "write": "Написать сообщение ✉️",
        "anon": "Отправить анонимно 👤",
        "cancel": "Отмена ❌",
        "reply": "Ответить 📨"
    },
    "en": {
        "choose_lang": "Choose language 🇬🇧",
        "prompt_anonymous": "Send a message or media. It will be anonymous 👤",
        "prompt_normal": "Send a message or media ✉️",
        "sent": "Your message has been sent ✅",
        "action": "Choose an action:",
        "write": "Write message ✉️",
        "anon": "Send anonymously 👤",
        "cancel": "Cancel ❌",
        "reply": "Reply 📨"
    },
    "uz": {
        "choose_lang": "Tilni tanlang 🇺🇿",
        "prompt_anonymous": "Xabar yoki media yuboring. U anonim bo'ladi 👤",
        "prompt_normal": "Xabar yoki media yuboring ✉️",
        "sent": "Xabaringiz yuborildi ✅",
        "action": "Harakatni tanlang:",
        "write": "Xabar yozish ✉️",
        "anon": "Anonim yuborish 👤",
        "cancel": "Bekor qilish ❌",
        "reply": "Javob berish 📨"
    },
    "ar": {
        "choose_lang": "اختر اللغة 🇸🇦",
        "prompt_anonymous": "أرسل رسالة أو وسائط. ستكون مجهولة 👤",
        "prompt_normal": "أرسل رسالة أو وسائط ✉️",
        "sent": "تم إرسال رسالتك ✅",
        "action": "اختر الإجراء:",
        "write": "اكتب رسالة ✉️",
        "anon": "إرسال مجهول 👤",
        "cancel": "إلغاء ❌",
        "reply": "رد 📨"
    }
}

# Старт
@bot.message_handler(commands=["start"])
def start(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add("🇷🇺", "🇬🇧", "🇺🇿", "🇸🇦")
    msg = bot.send_message(message.chat.id, "Выберите язык 🌐", reply_markup=markup)
    users[message.chat.id] = {"lang_msg_id": msg.message_id}

# Выбор языка
@bot.message_handler(func=lambda m: m.chat.id in users and "lang_msg_id" in users[m.chat.id])
def set_language(message):
    lang_map = {"🇷🇺": "ru", "🇬🇧": "en", "🇺🇿": "uz", "🇸🇦": "ar"}
    lang = lang_map.get(message.text, "ru")
    users[message.chat.id]["lang"] = lang
    try: bot.delete_message(message.chat.id, users[message.chat.id]["lang_msg_id"])
    except: pass
    send_action_buttons(message.chat.id)

# Кнопки действий для пользователя
def send_action_buttons(chat_id):
    lang = users[chat_id]["lang"]
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(text=texts[lang]["write"], callback_data="write"),
        types.InlineKeyboardButton(text=texts[lang]["anon"], callback_data="anon")
    )
    bot.send_message(chat_id, texts[lang]["action"], reply_markup=markup)

# Обработка выбора действия
@bot.callback_query_handler(func=lambda c: c.data in ["write", "anon"])
def handle_action(call):
    chat_id = call.message.chat.id
    lang = users[chat_id]["lang"]
    users[chat_id]["current_action"] = call.data

    prompt_text = texts[lang]["prompt_normal"] if call.data == "write" else texts[lang]["prompt_anonymous"]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(texts[lang]["cancel"])

    sent_msg = bot.send_message(chat_id, prompt_text, reply_markup=markup)
    users[chat_id]["last_prompt_id"] = sent_msg.message_id
    try: bot.delete_message(chat_id, call.message.message_id)
    except: pass

# Обработка отмены
@bot.message_handler(func=lambda m: m.text in [texts[users[m.chat.id]["lang"]]["cancel"] for m in users if "lang" in users[m.chat.id]])
def handle_cancel(message):
    chat_id = message.chat.id
    try: bot.delete_message(chat_id, users[chat_id]["last_prompt_id"])
    except: pass
    send_action_buttons(chat_id)

# Получение текста или медиа
@bot.message_handler(content_types=["text", "photo", "video", "document", "sticker", "audio", "voice"])
def handle_user_message(message):
    chat_id = message.chat.id
    if chat_id not in users or "current_action" not in users[chat_id]:
        return

    lang = users[chat_id]["lang"]
    action = users[chat_id]["current_action"]

    try: bot.delete_message(chat_id, users[chat_id]["last_prompt_id"])
    except: pass

    # Отправка админу
    user_info = f"@{message.from_user.username} (id: {message.from_user.id})"
    anon_text = "анонимное " if action=="anon" else ""
    msg_to_admin = bot.send_message(
        ADMIN_ID, f"Новое {anon_text}сообщение от {user_info}"
    )

    # Кнопка "Ответить" админу
    reply_markup = types.InlineKeyboardMarkup()
    reply_markup.add(types.InlineKeyboardButton(text=texts["ru"]["reply"], callback_data=f"reply_{message.from_user.id}"))
    
    if message.content_type == "text":
        bot.send_message(ADMIN_ID, message.text, reply_markup=reply_markup)
    else:
        fwd = bot.forward_message(ADMIN_ID, chat_id, message.message_id)
        bot.send_message(ADMIN_ID, "Ответить на это сообщение:", reply_markup=reply_markup)

    # Подтверждение пользователю
    bot.send_message(chat_id, texts[lang]["sent"])
    send_action_buttons(chat_id)

# Обработка нажатия "Ответить" админом
@bot.callback_query_handler(func=lambda c: c.data.startswith("reply_"))
def handle_admin_reply(call):
    target_id = int(call.data.split("_")[1])
    pending_admin_reply[ADMIN_ID] = target_id
    bot.send_message(ADMIN_ID, f"Напишите ответ пользователю {target_id}:")

# Отправка ответа админа пользователю
@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and ADMIN_ID in pending_admin_reply)
def send_admin_reply(message):
    target_id = pending_admin_reply.pop(ADMIN_ID)
    if message.content_type == "text":
        bot.send_message(target_id, f"Ответ от администратора:\n{message.text}")
    else:
        bot.forward_message(target_id, ADMIN_ID, message.message_id)

bot.infinity_polling()
