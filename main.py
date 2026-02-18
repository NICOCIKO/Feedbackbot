import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

TOKEN = "8341977158:AAGB6u5WiQ0LHrrEigv5NdrlSxtR9m33gKo"
ADMIN_ID = 7924774037

bot = telebot.TeleBot(TOKEN)

# Хранилище пользователей и сообщений
users_lang = {}  # user_id: 'ru'/'en'
pending_messages = {}  # user_id: message info

# Тексты на двух языках
TEXTS = {
    'start': {
        'ru': "Привет! Выберите язык.",
        'en': "Hello! Choose your language."
    },
    'choose_action': {
        'ru': "Выберите действие 📝",
        'en': "Choose an action 📝"
    },
    'send_msg': {
        'ru': "Отправьте сообщение или медиа.",
        'en': "Send a message or media."
    },
    'send_anon': {
        'ru': "Отправьте сообщение или медиа. Оно будет анонимным.",
        'en': "Send a message or media. It will be anonymous."
    },
    'sent': {
        'ru': "Сообщение отправлено ✅",
        'en': "Message sent ✅"
    },
    'cancel': {
        'ru': "❌ Отмена",
        'en': "❌ Cancel"
    },
    'reply_btn': {
        'ru': "Ответить 💬",
        'en': "Reply 💬"
    }
}

# --- Старт бота ---
@bot.message_handler(commands=['start'])
def start(msg: Message):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
    )
    sent = bot.send_message(msg.chat.id, TEXTS['start']['ru'], reply_markup=markup)
    # запоминаем сообщение чтобы удалить после выбора языка
    pending_messages[msg.chat.id] = {'msg_id': sent.message_id, 'type': 'lang'}

# --- Обработка выбора языка ---
@bot.callback_query_handler(func=lambda c: c.data.startswith('lang_'))
def choose_language(c):
    lang = c.data.split('_')[1]
    users_lang[c.from_user.id] = lang
    # удаляем сообщение с выбором языка
    bot.delete_message(c.from_user.id, pending_messages[c.from_user.id]['msg_id'])
    del pending_messages[c.from_user.id]

    # Отправляем выбор действия
    send_action_buttons(c.from_user.id)

# --- Кнопки действия для пользователей ---
def send_action_buttons(user_id):
    lang = users_lang[user_id]
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("📝 Написать сообщение" if lang=='ru' else "📝 Send message", callback_data="write_msg"),
        InlineKeyboardButton("🕵️ Анонимно" if lang=='ru' else "🕵️ Anonymous", callback_data="write_anon")
    )
    sent = bot.send_message(user_id, TEXTS['choose_action'][lang], reply_markup=markup)
    pending_messages[user_id] = {'msg_id': sent.message_id, 'type': 'action'}

# --- Обработка выбора действия ---
@bot.callback_query_handler(func=lambda c: c.data.startswith('write_'))
def write_action(c):
    user_id = c.from_user.id
    lang = users_lang[user_id]
    action = c.data.split('_')[1]  # msg or anon
    text = TEXTS['send_msg'][lang] if action == 'msg' else TEXTS['send_anon'][lang]
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(TEXTS['cancel'][lang], callback_data='cancel'))

    sent = bot.send_message(user_id, text, reply_markup=markup)
    pending_messages[user_id] = {'msg_id': sent.message_id, 'type': 'writing', 'anon': action=='anon'}

# --- Отмена ---
@bot.callback_query_handler(func=lambda c: c.data == 'cancel')
def cancel(c):
    user_id = c.from_user.id
    lang = users_lang[user_id]
    # удаляем сообщение ввода
    bot.delete_message(user_id, pending_messages[user_id]['msg_id'])
    del pending_messages[user_id]
    # показываем снова выбор действия
    send_action_buttons(user_id)

# --- Получение сообщений от пользователя ---
@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'audio', 'voice'])
def handle_user_message(msg: Message):
    user_id = msg.from_user.id
    if user_id not in pending_messages:
        return  # Игнорируем если пользователь не в процессе отправки

    lang = users_lang[user_id]
    is_anon = pending_messages[user_id].get('anon', False)
    # удаляем сообщение ввода у пользователя
    bot.delete_message(user_id, pending_messages[user_id]['msg_id'])
    del pending_messages[user_id]

    # отправляем админу
    if is_anon:
        caption = f"[Анонимное сообщение]\nID: {msg.from_user.id}\nUsername: @{msg.from_user.username or 'none'}"
    else:
        caption = f"[Сообщение от пользователя]\nID: {msg.from_user.id}\nUsername: @{msg.from_user.username or 'none'}"

    if msg.content_type == 'text':
        bot.send_message(ADMIN_ID, f"{caption}\n\n{msg.text}", reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton(TEXTS['reply_btn'][users_lang.get(ADMIN_ID,'ru')], callback_data=f"reply_{user_id}")
        ))
    else:
        # медиа
        bot.forward_message(ADMIN_ID, user_id, msg.message_id)
        bot.send_message(ADMIN_ID, caption, reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton(TEXTS['reply_btn'][users_lang.get(ADMIN_ID,'ru')], callback_data=f"reply_{user_id}")
        ))

    # уведомление пользователю
    bot.send_message(user_id, TEXTS['sent'][lang])
    # снова показываем кнопки действий
    send_action_buttons(user_id)

# --- Ответ админа ---
@bot.callback_query_handler(func=lambda c: c.data.startswith('reply_'))
def admin_reply(c):
    target_id = int(c.data.split('_')[1])
    users_lang.setdefault(target_id, 'ru')  # default lang
    # просим админа ввести сообщение
    sent = bot.send_message(ADMIN_ID, f"Введите ответ для ID {target_id}")
    pending_messages[ADMIN_ID] = {'msg_id': sent.message_id, 'reply_to': target_id}

# --- Получение ответа админа ---
@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID)
def handle_admin_reply(msg: Message):
    if ADMIN_ID not in pending_messages or 'reply_to' not in pending_messages[ADMIN_ID]:
        return
    target_id = pending_messages[ADMIN_ID]['reply_to']
    del pending_messages[ADMIN_ID]
    lang = users_lang.get(target_id, 'ru')
    # Отправка пользователю
    bot.send_message(target_id, f"💬 Ответ администратора:\n{msg.text}", reply_markup=InlineKeyboardMarkup().add(
        InlineKeyboardButton(TEXTS['reply_btn'][lang], callback_data="write_msg")
    ))

bot.infinity_polling()
