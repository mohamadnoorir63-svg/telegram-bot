import telebot
from telebot import types
from datetime import datetime, timedelta

TOKEN = "7462131830:AAENzKipQzuxQ4UYkl9vcVgmmfDMKMUvZi8"
bot = telebot.TeleBot(TOKEN)

# دیتابیس ساده برای شارژ
group_expiry = {}

# ======================
# شروع در پیوی (پنل مدیریت)
# ======================
@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.type == "private":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("⏳ شارژ گروه", "❓ راهنما")
        bot.send_message(message.chat.id, "👋 خوش آمدید! این پنل فقط مخصوص مدیر است.", reply_markup=markup)
    else:
        bot.reply_to(message, "برای استفاده از پنل مدیریت به پیوی من بیا.")

# ======================
# دستورات در پیوی مدیر
# ======================
@bot.message_handler(func=lambda m: m.chat.type == "private")
def private_handler(message):
    text = message.text

    if text == "⏳ شارژ گروه":
        bot.send_message(message.chat.id, "مدت شارژ را انتخاب کن:\n/charge7 (7 روز)\n/charge30 (30 روز)")

    elif text == "❓ راهنما":
        bot.send_message(message.chat.id, """
📖 راهنما:
دستورات گروه:
- قفل لینک
- باز کردن لینک
- بن (ریپلای)
- سکوت (ریپلای)
- آمار
- ایدی
- ساعت
- تاریخ
- لفت بده
""")

    elif text.startswith("/charge7"):
        group_id = -100123456789  # آیدی گروهت رو اینجا بذار
        group_expiry[group_id] = datetime.now() + timedelta(days=7)
        bot.send_message(message.chat.id, "✅ گروه برای 7 روز شارژ شد.")

    elif text.startswith("/charge30"):
        group_id = -100123456789
        group_expiry[group_id] = datetime.now() + timedelta(days=30)
        bot.send_message(message.chat.id, "✅ گروه برای 30 روز شارژ شد.")

# ======================
# دستورات داخل گروه
# ======================
@bot.message_handler(func=lambda m: m.chat.type in ["group", "supergroup"])
def group_handler(message):
    cid = message.chat.id
    text = message.text

    # اگر شارژ گروه تمام شده
    if cid in group_expiry and datetime.now() > group_expiry[cid]:
        bot.send_message(cid, "⛔️ شارژ گروه تمام شده. لطفا با مدیر تماس بگیرید.")
        return

    if text == "قفل لینک":
        bot.send_message(cid, "🔒 لینک‌ها قفل شدند.")

    elif text == "باز کردن لینک":
        bot.send_message(cid, "🔓 لینک‌ها آزاد شدند.")

    elif text == "ایدی":
        bot.send_message(cid, f"🆔 ایدی شما: {message.from_user.id}\n🆔 ایدی گروه: {cid}")

    elif text == "آمار":
        members = bot.get_chat_members_count(cid)
        bot.send_message(cid, f"👥 تعداد اعضا: {members}")

    elif text == "ساعت":
        bot.send_message(cid, f"⏰ {datetime.now().strftime('%H:%M:%S')}")

    elif text == "تاریخ":
        bot.send_message(cid, f"📅 {datetime.now().strftime('%Y-%m-%d')}")

    elif text == "لفت بده":
        bot.send_message(cid, "👋 خداحافظ، من از گروه خارج می‌شوم.")
        bot.leave_chat(cid)

# ======================
print("🤖 Bot is running...")
bot.infinity_polling()
