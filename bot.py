import telebot
from telebot import types
from datetime import datetime, timedelta
import re

# 🔑 توکن ربات
TOKEN = "7462131830:AAENzKipQzuxQ4UYkl9vcVgmmfDMKMUvZi8"
# 👑 آیدی عددی سودو (مدیر اصلی ربات)
SUDO_ID = 7089376754  # آیدی خودت رو اینجا بزار

bot = telebot.TeleBot(TOKEN)

# دیتابیس ساده
group_expiry = {}       # تاریخ انقضا هر گروه
welcome_messages = {}   # پیام خوشامد هر گروه
all_groups = set()      # لیست گروه‌ها

# وضعیت قفل‌ها
lock_links = {}
lock_stickers = {}
lock_group = {}

# ======================
# /start → پنل مدیریت در پیوی سودو
# ======================
@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.type == "private" and message.from_user.id == SUDO_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("📊 آمار گروه‌ها", "📩 ارسال پیام")
        markup.add("⏳ شارژ گروه", "💬 تنظیم خوشامد")
        bot.send_message(message.chat.id, "👑 پنل مدیریت سودو", reply_markup=markup)
    else:
        bot.reply_to(message, "✅ ربات فعال است!")

# ======================
# پنل سودو
# ======================
@bot.message_handler(func=lambda m: m.chat.type == "private" and m.from_user.id == SUDO_ID)
def sudo_panel(message):
    text = message.text

    if text == "📊 آمار گروه‌ها":
        if not group_expiry:
            bot.send_message(message.chat.id, "❌ هیچ گروهی ثبت نشده")
        else:
            stats = "\n".join([f"{gid} : تا {exp.strftime('%Y-%m-%d')}" for gid, exp in group_expiry.items()])
            bot.send_message(message.chat.id, "📊 آمار گروه‌ها:\n" + stats)

    elif text == "📩 ارسال پیام":
        bot.send_message(message.chat.id, "✏️ پیام خود را بفرست تا به همه گروه‌ها ارسال شود.")
        bot.register_next_step_handler(message, broadcast)

    elif text == "⏳ شارژ گروه":
        bot.send_message(message.chat.id, "فرمت دستور:\n/charge group_id روز")

    elif text == "💬 تنظیم خوشامد":
        bot.send_message(message.chat.id, "فرمت دستور:\n/welcome group_id متن خوشامد")

# ======================
# ارسال پیام همگانی
# ======================
def broadcast(message):
    for gid in all_groups:
        try:
            bot.send_message(gid, f"📢 پیام مدیر:\n{message.text}")
        except:
            pass
    bot.send_message(message.chat.id, "✅ پیام ارسال شد.")

# ======================
# شارژ گروه (فقط سودو)
# ======================
@bot.message_handler(commands=['charge'])
def charge_group(message):
    if message.from_user.id != SUDO_ID:
        return
    try:
        _, group_id, days = message.text.split()
        group_expiry[int(group_id)] = datetime.now() + timedelta(days=int(days))
        all_groups.add(int(group_id))
        bot.send_message(message.chat.id, f"✅ گروه {group_id} برای {days} روز شارژ شد.")
    except:
        bot.send_message(message.chat.id, "❌ فرمت درست:\n/charge group_id روز")

# ======================
# خوشامدگویی
# ======================
@bot.message_handler(commands=['welcome'])
def set_welcome(message):
    if message.from_user.id != SUDO_ID:
        return
    try:
        _, group_id, *text = message.text.split()
        welcome_messages[int(group_id)] = " ".join(text)
        bot.send_message(message.chat.id, f"✅ پیام خوشامد گروه {group_id} تغییر کرد.")
    except:
        bot.send_message(message.chat.id, "❌ فرمت درست:\n/welcome group_id متن")

@bot.message_handler(content_types=['new_chat_members'])
def greet_new_member(message):
    cid = message.chat.id
    if cid in group_expiry and datetime.now() < group_expiry[cid]:
        text = welcome_messages.get(cid, "👋 خوش آمدید!")
        bot.send_message(cid, text)

# ======================
# دستورات داخل گروه
# ======================
@bot.message_handler(func=lambda m: m.chat.type in ["group", "supergroup"])
def group_handler(message):
    cid = message.chat.id
    all_groups.add(cid)
    text = message.text

    # بررسی شارژ گروه
    if cid not in group_expiry:
        return
    if datetime.now() > group_expiry[cid]:
        bot.send_message(cid, "⛔️ شارژ گروه تمام شد. ربات لفت می‌دهد.")
        bot.leave_chat(cid)
        return

    # دستورات
    if text == "ساعت":
        bot.send_message(cid, datetime.now().strftime("⏰ %H:%M:%S"))

    elif text == "تاریخ":
        bot.send_message(cid, datetime.now().strftime("📅 %Y-%m-%d"))

    elif text == "آمار":
        members = bot.get_chat_members_count(cid)
        bot.send_message(cid, f"👥 تعداد اعضا: {members}")

    elif text == "لفت بده" and message.from_user.id == SUDO_ID:
        bot.send_message(cid, "👋 خداحافظ")
        bot.leave_chat(cid)

    elif text == "قفل لینک":
        lock_links[cid] = True
        bot.send_message(cid, "🔒 لینک‌ها قفل شدند.")

    elif text == "باز کردن لینک":
        lock_links[cid] = False
        bot.send_message(cid, "🔓 لینک‌ها آزاد شدند.")

    elif text == "قفل استیکر":
        lock_stickers[cid] = True
        bot.send_message(cid, "🔒 استیکرها قفل شدند.")

    elif text == "باز کردن استیکر":
        lock_stickers[cid] = False
        bot.send_message(cid, "🔓 استیکرها آزاد شدند.")

    elif text == "قفل گروه":
        try:
            bot.set_chat_permissions(cid, types.ChatPermissions(can_send_messages=False))
            lock_group[cid] = True
            bot.send_message(cid, "🔒 گروه قفل شد. فقط مدیرها پیام می‌دهند.")
        except:
            bot.send_message(cid, "⚠️ ربات باید ادمین باشد.")

    elif text == "باز کردن گروه":
        try:
            bot.set_chat_permissions(cid, types.ChatPermissions(can_send_messages=True))
            lock_group[cid] = False
            bot.send_message(cid, "🔓 گروه باز شد.")
        except:
            bot.send_message(cid, "⚠️ ربات باید ادمین باشد.")

    elif text == "پاکسازی" and message.from_user.id == SUDO_ID:
        try:
            for i in range(message.message_id - 50, message.message_id):
                bot.delete_message(cid, i)
            bot.send_message(cid, "🧹 گروه پاکسازی شد (۵۰ پیام آخر حذف شد).")
        except:
            bot.send_message(cid, "⚠️ ربات باید دسترسی حذف پیام داشته باشد.")

# ======================
# فیلتر پیام‌ها
# ======================
@bot.message_handler(func=lambda m: True, content_types=['text', 'sticker'])
def filters(message):
    cid = message.chat.id
    if cid in lock_links and lock_links[cid]:
        if message.text and re.search(r"(https?://|t\.me/)", message.text):
            try:
                bot.delete_message(cid, message.message_id)
            except:
                pass

    if cid in lock_stickers and lock_stickers[cid]:
        if message.content_type == 'sticker':
            try:
                bot.delete_message(cid, message.message_id)
            except:
                pass

# ======================
print("🤖 Bot is running...")
bot.infinity_polling()
