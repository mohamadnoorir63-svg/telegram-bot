import telebot
from telebot import types
from datetime import datetime, timedelta

# ---------------------------
TOKEN = "7462131830:AAENzKipQzuxQ4UYkl9vcVgmmfDMKMUvZi8"
SUDO_ID = 7089376754  # آیدی عددی مدیر اصلی
bot = telebot.TeleBot(TOKEN)
# ---------------------------

# دیتابیس ساده
groups = {}        # {chat_id: expire_date}
welcomes = {}      # {chat_id: "welcome text"}
lock_link = {}     # {chat_id: True/False}

# ---------------------------
# استارت در پیوی
@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.type == "private":
        if message.from_user.id == SUDO_ID:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("📊 آمار گروه‌ها", "➕ شارژ گروه")
            markup.add("✉️ ارسال پیام", "⚙️ مدیریت خوشامد")
            bot.send_message(message.chat.id, "🔐 پنل مدیریتی:", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "سلام 👋\nبرای استفاده، منو به گروه اضافه کنید و شارژ کنید.")

# ---------------------------
# شارژ گروه (فقط سودو)
@bot.message_handler(commands=['charge'])
def charge_group(message):
    if message.from_user.id != SUDO_ID:
        return
    try:
        parts = message.text.split()
        if len(parts) != 3:
            bot.reply_to(message, "❌ فرمت درست:\n/charge group_id روز")
            return
        group_id = int(parts[1])
        days = int(parts[2])
        expire = datetime.now() + timedelta(days=days)
        groups[group_id] = expire
        bot.send_message(message.chat.id, f"✅ گروه {group_id} برای {days} روز شارژ شد.")
        bot.send_message(group_id, f"⚡️ گروه برای {days} روز شارژ شد.")
    except Exception as e:
        bot.reply_to(message, f"خطا: {e}")

# ---------------------------
# خوشامدگویی
@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    chat_id = message.chat.id
    if chat_id not in groups or groups[chat_id] < datetime.now():
        return
    text = welcomes.get(chat_id, "خوش آمدید 🌹")
    for member in message.new_chat_members:
        bot.send_message(chat_id, f"{member.first_name} {text}")

# ---------------------------
# دستورات متنی داخل گروه
@bot.message_handler(func=lambda m: m.chat.type in ["group", "supergroup"])
def group_commands(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # اول بررسی کنیم گروه شارژ هست یا نه
    if chat_id not in groups or groups[chat_id] < datetime.now():
        return

    text = message.text.lower()

    # آمار
    if text == "آمار":
        count = bot.get_chat_members_count(chat_id)
        bot.reply_to(message, f"👥 تعداد اعضای گروه: {count}")

    # ساعت
    elif text == "ساعت":
        now = datetime.now().strftime("%H:%M:%S")
        bot.reply_to(message, f"⏰ ساعت: {now}")

    # تاریخ
    elif text == "تاریخ":
        today = datetime.now().strftime("%Y-%m-%d")
        bot.reply_to(message, f"📅 تاریخ: {today}")

    # قفل لینک
    elif text == "قفل لینک":
        lock_link[chat_id] = True
        bot.reply_to(message, "✅ لینک‌ها قفل شدند.")

    elif text == "باز کردن لینک":
        lock_link[chat_id] = False
        bot.reply_to(message, "🔓 لینک‌ها آزاد شدند.")

# ---------------------------
# حذف لینک وقتی قفل باشه
@bot.message_handler(content_types=['text'])
def block_links(message):
    chat_id = message.chat.id
    if message.chat.type in ["group", "supergroup"]:
        if lock_link.get(chat_id) and ("http://" in message.text or "https://" in message.text or "t.me" in message.text):
            try:
                bot.delete_message(chat_id, message.message_id)
            except:
                pass

# ---------------------------
print("Bot is running...")
bot.infinity_polling()
