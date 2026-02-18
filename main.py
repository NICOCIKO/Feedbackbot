import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os

TOKEN = "8341977158:AAGB6u5WiQ0LHrrEigv5NdrlSxtR9m33gKo"
ADMIN_ID = 7924774037

bot = telebot.TeleBot(TOKEN)

DATA_FILE = "users.json"

# ===== Загрузка пользователей =====

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        users = json.load(f)
else:
    users = {}

def save_users():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4)

# ===== Переводы =====

texts = {
    "ru": {
        "choose_lang": "🌍 Выберите язык:",
        "welcome": "👋 Добро пожаловать!\n\nВыберите действие:",
        "write": "✍️ Написать сообщение",
        "anon": "🕵️ Анонимное сообщение",
        "change_lang": "🌍 Сменить язык",
        "enter_msg": "✍️ Введите сообщение:",
        "enter_anon": "🕵️ Введите анонимное сообщение:",
        "sent": "✅ Сообщение отправлено!",
        "reply_from_admin": "📩 Ответ от администратора:"
    },
    "en": {
        "choose_lang": "🌍 Choose language:",
        "welcome": "👋 Welcome!\n\nChoose action:",
        "write": "✍️ Send message",
        "anon": "🕵️ Anonymous message",
        "change_lang": "🌍 Change language",
        "enter_msg": "✍️ Enter message:",
        "enter_anon": "🕵️ Enter anonymous message:",
        "sent": "✅ Message sent!",
        "reply_from_admin": "📩 Reply from admin:"
    },
    "uz": {
        "choose_lang": "🌍 Tilni tanlang:",
        "welcome": "👋 Xush kelibsiz!\n\nAmalni tanlang:",
        "write": "✍️ Xabar yuborish",
        "anon": "🕵️ Anonim xabar",
        "change_lang": "🌍 Tilni o‘zgartirish",
        "enter_msg": "✍️ Xabarni kiriting:",
        "enter_anon": "🕵️ Anonim xabarni kiriting:",
        "sent": "✅ Xabar yuborildi!",
        "reply_from_admin": "📩 Administrator javobi:"
    },
    "ar": {
        "choose_lang": "🌍 اختر اللغة:",
        "welcome": "👋 مرحبًا!\n\nاختر إجراء:",
        "write": "✍️ إرسال رسالة",
        "anon": "🕵️ رسالة مجهولة",
        "change_lang": "🌍 تغيير اللغة",
        "enter_msg": "✍️ اكتب الرسالة:",
        "enter_anon": "🕵️ اكتب الرسالة المجهولة:",
        "sent": "✅ تم الإرسال!",
        "reply_from_admin": "📩 رد من المشرف:"
    }
}

# ===== Меню =====

def language_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        InlineKeyboardButton("🇺🇿 O‘zbek", callback_data="lang_uz"),
        InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar")
    )
    return markup

def main_menu(lang):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(texts[lang]["write"], callback_data="write"),
        InlineKeyboardButton(texts[lang]["anon"], callback_data="anon"),
        InlineKeyboardButton(texts[lang]["change_lang"], callback_data="change_lang")
    )
    return markup

# ===== START =====

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, texts["ru"]["choose_lang"], reply_markup=language_menu())

# ===== CALLBACK =====

@bot.callback_query_handler(func=lambda c: True)
def callback_handler(call):
    user_id = str(call.from_user.id)

    # ===== Выбор языка =====
    if call.data.startswith("lang_"):
        lang = call.data.split("_")[1]

        users[user_id] = {
            "username": call.from_user.username or "NoUsername",
            "lang": lang
        }
        save_users()

        bot.delete_message(call.message.chat.id, call.message.message_id)

        bot.send_message(
            call.message.chat.id,
            texts[lang]["welcome"],
            reply_markup=main_menu(lang)
        )
        return

    user = users.get(user_id)
    if not user:
        return

    lang = user["lang"]

    bot.delete_message(call.message.chat.id, call.message.message_id)

    if call.data == "write":
        msg = bot.send_message(user_id, texts[lang]["enter_msg"])
        bot.register_next_step_handler(msg, process_message, False)

    elif call.data == "anon":
        msg = bot.send_message(user_id, texts[lang]["enter_anon"])
        bot.register_next_step_handler(msg, process_message, True)

    elif call.data == "change_lang":
        bot.send_message(user_id, texts[lang]["choose_lang"], reply_markup=language_menu())

# ===== Отправка администратору =====

def process_message(message, is_anon):
    user_id = str(message.from_user.id)
    user = users.get(user_id)
    if not user:
        return

    lang = user["lang"]
    username = user["username"]

    header = (
        f"🕵️ ANONYMOUS\n🆔 {user_id}\n\n"
        if is_anon else
        f"📩 MESSAGE\n👤 @{username}\n🆔 {user_id}\n\n"
    )

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("↩️ Reply", callback_data=f"reply_{user_id}")
    )

    if message.content_type == "text":
        bot.send_message(ADMIN_ID, header + message.text, reply_markup=markup)

    elif message.content_type == "photo":
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=header, reply_markup=markup)

    elif message.content_type == "video":
        bot.send_video(ADMIN_ID, message.video.file_id, caption=header, reply_markup=markup)

    bot.send_message(user_id, texts[lang]["sent"], reply_markup=main_menu(lang))

# ===== Ответ админа =====

@bot.callback_query_handler(func=lambda c: c.data.startswith("reply_"))
def admin_reply(call):
    if call.from_user.id != ADMIN_ID:
        return

    user_id = call.data.split("_")[1]

    msg = bot.send_message(ADMIN_ID, "✍️ Введите ответ:")
    bot.register_next_step_handler(msg, send_admin_reply, user_id)

def send_admin_reply(message, user_id):
    user = users.get(user_id)
    if not user:
        return

    lang = user["lang"]

    if message.content_type == "text":
        bot.send_message(user_id, f"{texts[lang]['reply_from_admin']}\n\n{message.text}")

    elif message.content_type == "photo":
        bot.send_photo(user_id, message.photo[-1].file_id,
                       caption=texts[lang]["reply_from_admin"])

    bot.send_message(ADMIN_ID, "✅ Ответ отправлен")

bot.infinity_polling()
