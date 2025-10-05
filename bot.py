# -*- coding: utf-8 -*-
import telebot, os, re
from telebot import types
from datetime import datetime
import pytz

# ================== تنظیمات ==================
TOKEN   = os.environ.get("BOT_TOKEN")   # توکن ربات از Config Vars
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))  # آیدی سودو اصلی
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
# ============================================

HELP_TEXT = """
📖 لیست دستورات:

⏰ ساعت | 🆔 ایدی | 📊 آمار | 📎 لینک
🛠 وضعیت ربات
🎉 خوشامد روشن / خاموش
✍️ خوشامد متن [متن]
🖼 ثبت عکس (روی عکس ریپلای کن)
🔒 قفل لینک / باز کردن لینک
🧷 قفل استیکر / باز کردن استیکر
🤖 قفل ربات / باز کردن ربات
🚫 قفل تبچی / باز کردن تبچی
🔐 قفل گروه / باز کردن گروه
🖼 قفل عکس / باز کردن عکس
🎥 قفل ویدیو / باز کردن ویدیو
🎭 قفل گیف / باز کردن گیف
📎 قفل فایل / باز کردن فایل
🎶 قفل موزیک / باز کردن موزیک
🎙 قفل ویس / باز کردن ویس
🔄 قفل فوروارد / باز کردن فوروارد
🚫 بن / ✅ حذف بن   (ریپلای)
🔕 سکوت / 🔊 حذف سکوت (ریپلای)
⚠️ اخطار / حذف اخطار (ریپلای)
👑 مدیر / ❌ حذف مدیر (ریپلای)
📌 پن / ❌ حذف پن    (ریپلای)
📋 لیست مدیران گروه | 📋 لیست مدیران ربات
🧹 پاکسازی              (تا ۹۹۹۹ پیام)
🧹 حذف [عدد]           (پاکسازی تعداد مشخص)
📢 ارسال                (فقط سودو)
➕ افزودن سودو [آیدی]
➖ حذف سودو [آیدی]
🚪 لفت بده              (فقط سودو)
🧑‍🤝‍🧑 من کیم
🧾 این کیه (ریپلای)
🏷 لقب [متن] (ریپلای) | لقب
"""

# ========= سودو / ادمین =========
sudo_ids = {SUDO_ID}
def is_sudo(uid): return uid in sudo_ids

def is_admin(chat_id, user_id):
    if is_sudo(user_id): return True
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator","creator")
    except:
        return False

def cmd_text(m): 
    return (getattr(m,"text",None) or getattr(m,"caption",None) or "").strip()

# ========= ذخیره گروه‌ها برای ارسال همگانی =========
joined_groups=set()
@bot.my_chat_member_handler()
def track_groups(upd):
    try:
        chat=upd.chat
        if chat and chat.type in ("group","supergroup"):
            joined_groups.add(chat.id)
    except:
        pass

# ========= دستورات پایه =========
@bot.message_handler(func=lambda m: cmd_text(m)=="راهنما")
def help_cmd(m): 
    bot.reply_to(m,HELP_TEXT)

@bot.message_handler(func=lambda m: cmd_text(m)=="ساعت")
def time_cmd(m):
    now_utc=datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S")
    now_teh=datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y-%m-%d %H:%M:%S")
    bot.reply_to(m,f"⏰ ساعت UTC: {now_utc}\n⏰ ساعت تهران: {now_teh}")

@bot.message_handler(func=lambda m: cmd_text(m)=="ایدی")
def id_cmd(m):
    try:
        photos=bot.get_user_profile_photos(m.from_user.id,limit=1)
        caption=f"🆔 شما: <code>{m.from_user.id}</code>\n🆔 گروه: <code>{m.chat.id}</code>"
        if photos.total_count>0:
            bot.send_photo(m.chat.id,photos.photos[0][-1].file_id,caption=caption)
        else:
            bot.reply_to(m,caption)
    except:
        bot.reply_to(m,f"🆔 شما: <code>{m.from_user.id}</code>\n🆔 گروه: <code>{m.chat.id}</code>")

@bot.message_handler(func=lambda m: cmd_text(m)=="آمار")
def stats(m):
    try: count=bot.get_chat_member_count(m.chat.id)
    except: count="نامشخص"
    bot.reply_to(m,f"📊 اعضای گروه: {count}")

@bot.message_handler(func=lambda m: cmd_text(m)=="لینک")
def group_link(m):
    try:
        link=bot.export_chat_invite_link(m.chat.id)
        bot.reply_to(m,f"📎 لینک گروه:\n{link}")
    except:
        bot.reply_to(m,"❗ نتوانستم لینک بگیرم. (بات باید ادمین با مجوز دعوت باشد)")# ========= خوشامد =========
welcome_enabled, welcome_texts, welcome_photos = {}, {}, {}

@bot.message_handler(content_types=['new_chat_members'])
def welcome(m):
    for u in m.new_chat_members:
        if not welcome_enabled.get(m.chat.id): continue
        name = u.first_name or ""
        date = datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y/%m/%d")
        time = datetime.now(pytz.timezone("Asia/Tehran")).strftime("%H:%M:%S")
        txt = f"• سلام {name} به گروه {m.chat.title} خوش آمدید 🌻\n\n📆 تاریخ : {date}\n⏰ ساعت : {time}"
        if m.chat.id in welcome_photos:
            bot.send_photo(m.chat.id,welcome_photos[m.chat.id],caption=txt)
        else:
            bot.send_message(m.chat.id,txt)

@bot.message_handler(func=lambda m: cmd_text(m)=="خوشامد روشن")
def w_on(m):
    if is_admin(m.chat.id,m.from_user.id):
        welcome_enabled[m.chat.id]=True
        bot.reply_to(m,"✅ خوشامد روشن شد.")

@bot.message_handler(func=lambda m: cmd_text(m)=="خوشامد خاموش")
def w_off(m):
    if is_admin(m.chat.id,m.from_user.id):
        welcome_enabled[m.chat.id]=False
        bot.reply_to(m,"❌ خوشامد خاموش شد.")

@bot.message_handler(func=lambda m: cmd_text(m).startswith("خوشامد متن"))
def w_txt(m):
    if is_admin(m.chat.id,m.from_user.id):
        welcome_texts[m.chat.id]=cmd_text(m).replace("خوشامد متن","",1).strip()
        bot.reply_to(m,"✍️ متن خوشامد ذخیره شد.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="ثبت عکس")
def w_photo(m):
    if is_admin(m.chat.id,m.from_user.id) and m.reply_to_message.photo:
        welcome_photos[m.chat.id]=m.reply_to_message.photo[-1].file_id
        bot.reply_to(m,"🖼 عکس خوشامد ذخیره شد.")

# ========= بقیه قابلیت‌ها =========
# قفل‌ها، بن/سکوت، اخطار، مدیر/حذف مدیر، پن، لقب و نقش، پاکسازی، وضعیت ربات،
# ارسال همگانی، مدیریت سودو، لفت بده و در پایان:

# ========= RUN =========
print("🤖 Bot is running...")
bot.infinity_polling()
