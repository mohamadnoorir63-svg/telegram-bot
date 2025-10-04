import telebot
from telebot import types
import time
from datetime import datetime

# ------------------ تنظیمات ------------------
TOKEN = "7462131830:AAENzKipQzuxQ4UYkl9vcVgmmfDMKMUvZi8"
SUDO_ID = 7089376754
bot = telebot.TeleBot(TOKEN)

groups = {}
welcome_settings = {}
welcome_content = {}
lock_links = {}
lock_stickers = {}
lock_group = {}
# ---------------------------------------------

# ✅ شارژ گروه (فارسی + انگلیسی)
@bot.message_handler(commands=['charge'])
def charge(message):
    if message.from_user.id != SUDO_ID:
        return
    try:
        days = int(message.text.split()[1])
        groups[str(message.chat.id)] = int(time.time()) + days * 86400
        bot.reply_to(message, f"✅ گروه برای {days} روز شارژ شد.")
    except:
        bot.reply_to(message, "❌ فرمت درست:\n/charge 30")

@bot.message_handler(func=lambda m: m.text and m.text.startswith("شارژ"))
def charge_farsi(message):
    if message.from_user.id != SUDO_ID: return
    try:
        days = int(message.text.split()[1])
        groups[str(message.chat.id)] = int(time.time()) + days * 86400
        bot.reply_to(message, f"✅ گروه برای {days} روز شارژ شد.")
    except:
        bot.reply_to(message, "❌ فرمت درست:\nشارژ 30")

# ✅ آمار
@bot.message_handler(commands=['stats'])
def stats(message):
    if not valid_group(message): return
    count = bot.get_chat_members_count(message.chat.id)
    bot.reply_to(message, f"👥 اعضای گروه: {count}")

@bot.message_handler(func=lambda m: m.text == "آمار")
def stats_farsi(message): stats(message)

# ✅ ساعت
@bot.message_handler(commands=['time'])
def time_cmd(message):
    if not valid_group(message): return
    now = datetime.now().strftime("%H:%M:%S")
    bot.reply_to(message, f"⏰ ساعت: {now}")

@bot.message_handler(func=lambda m: m.text == "ساعت")
def time_farsi(message): time_cmd(message)

# ✅ تاریخ
@bot.message_handler(commands=['date'])
def date_cmd(message):
    if not valid_group(message): return
    today = datetime.now().strftime("%Y-%m-%d")
    bot.reply_to(message, f"📅 تاریخ: {today}")

@bot.message_handler(func=lambda m: m.text == "تاریخ")
def date_farsi(message): date_cmd(message)

# ✅ ایدی
@bot.message_handler(commands=['id'])
def id_cmd(message):
    if not valid_group(message): return
    bot.reply_to(message, f"🆔 آیدی شما: {message.from_user.id}\n🆔 آیدی گروه: {message.chat.id}")

@bot.message_handler(func=lambda m: m.text == "ایدی")
def id_farsi(message): id_cmd(message)

# ✅ قفل لینک
@bot.message_handler(func=lambda m: m.text in ["قفل لینک","/locklink"])
def lock_link(message):
    if not valid_group(message): return
    lock_links[message.chat.id] = True
    bot.reply_to(message, "🔒 لینک‌ها قفل شدند.")

@bot.message_handler(func=lambda m: m.text in ["باز کردن لینک","/unlocklink"])
def unlock_link(message):
    if not valid_group(message): return
    lock_links[message.chat.id] = False
    bot.reply_to(message, "✅ لینک‌ها آزاد شدند.")

# ✅ قفل استیکر
@bot.message_handler(func=lambda m: m.text in ["قفل استیکر","/locksticker"])
def lock_sticker(message):
    if not valid_group(message): return
    lock_stickers[message.chat.id] = True
    bot.reply_to(message, "🔒 استیکرها قفل شدند.")

@bot.message_handler(func=lambda m: m.text in ["باز کردن استیکر","/unlocksticker"])
def unlock_sticker(message):
    if not valid_group(message): return
    lock_stickers[message.chat.id] = False
    bot.reply_to(message, "✅ استیکرها آزاد شدند.")

# ✅ قفل گروه
@bot.message_handler(func=lambda m: m.text in ["قفل گروه","/lockgroup"])
def lock_group_cmd(message):
    if not valid_group(message): return
    bot.set_chat_permissions(message.chat.id, types.ChatPermissions(can_send_messages=False))
    bot.reply_to(message, "🔒 گروه قفل شد.")

@bot.message_handler(func=lambda m: m.text in ["باز کردن گروه","/unlockgroup"])
def unlock_group_cmd(message):
    if not valid_group(message): return
    bot.set_chat_permissions(message.chat.id, types.ChatPermissions(can_send_messages=True))
    bot.reply_to(message, "✅ گروه باز شد.")

# ✅ پاکسازی
@bot.message_handler(func=lambda m: m.text in ["پاکسازی","/clear"])
def clear(message):
    if not valid_group(message): return
    if message.from_user.id != SUDO_ID: return
    deleted = 0
    for i in range(1, 51):
        try:
            bot.delete_message(message.chat.id, message.message_id - i)
            deleted += 1
        except: pass
    bot.reply_to(message, f"🧹 {deleted} پیام پاک شد.")

# ✅ راهنما
@bot.message_handler(func=lambda m: m.text in ["راهنما","/help"])
def help_cmd(message):
    if not valid_group(message): return
    bot.reply_to(message, """📖 دستورات:
🔹 آمار | ساعت | تاریخ | ایدی
🔹 قفل لینک / باز کردن لینک
🔹 قفل استیکر / باز کردن استیکر
🔹 قفل گروه / باز کردن گروه
🔹 پاکسازی (فقط سودو)
🔹 شارژ 30 (فقط سودو)
🔹 لفت بده (فقط سودو)
""")

# ✅ لفت
@bot.message_handler(func=lambda m: m.text in ["لفت بده","/leave"])
def leave_cmd(message):
    if message.from_user.id != SUDO_ID: return
    bot.send_message(message.chat.id, "👋 خداحافظ")
    bot.leave_chat(message.chat.id)

# ------------------- خوشامد -------------------
@bot.message_handler(content_types=['new_chat_members'])
def welcome_new(message):
    cid = str(message.chat.id)
    if not valid_group(message): return
    if welcome_settings.get(cid, True):
        if cid in welcome_content:
            content = welcome_content[cid]
            if "photo" in content:
                bot.send_photo(message.chat.id, content["photo"], caption=content.get("text", "👋 خوش آمدید!"))
            else:
                bot.send_message(message.chat.id, content.get("text", "👋 خوش آمدید!"))
        else:
            for user in message.new_chat_members:
                bot.send_message(message.chat.id, f"👋 خوش آمدید {user.first_name}")

@bot.message_handler(func=lambda m: m.text in ["خوشامد روشن","/welcomeon"])
def welcome_on(message):
    welcome_settings[str(message.chat.id)] = True
    bot.reply_to(message, "✅ خوشامد فعال شد.")

@bot.message_handler(func=lambda m: m.text in ["خوشامد خاموش","/welcomeoff"])
def welcome_off(message):
    welcome_settings[str(message.chat.id)] = False
    bot.reply_to(message, "❌ خوشامد خاموش شد.")

@bot.message_handler(func=lambda m: m.text == "ویرایش خوشامد" and m.reply_to_message)
def welcome_edit(message):
    cid = str(message.chat.id)
    if message.reply_to_message.photo:
        fid = message.reply_to_message.photo[-1].file_id
        caption = message.reply_to_message.caption or ""
        welcome_content[cid] = {"photo": fid, "text": caption}
        bot.reply_to(message, "✅ خوشامد با عکس ذخیره شد.")
    else:
        welcome_content[cid] = {"text": message.reply_to_message.text}
        bot.reply_to(message, "✅ خوشامد متنی ذخیره شد.")

# ------------------- فیلتر لینک/استیکر -------------------
@bot.message_handler(func=lambda m: True, content_types=['text','sticker'])
def filters(message):
    if not valid_group(message): return
    cid = message.chat.id
    if cid in lock_links and lock_links[cid]:
        if message.text and ("http" in message.text or "t.me" in message.text):
            try: bot.delete_message(cid, message.message_id)
            except: pass
    if cid in lock_stickers and lock_stickers[cid]:
        if message.content_type == 'sticker':
            try: bot.delete_message(cid, message.message_id)
            except: pass

# ------------------- Helper -------------------
def valid_group(message):
    gid = str(message.chat.id)
    return gid in groups and groups[gid] > int(time.time())

# ------------------- Run -------------------
print("🤖 Bot is running...")
bot.infinity_polling()
