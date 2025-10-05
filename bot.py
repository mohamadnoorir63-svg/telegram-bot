# -*- coding: utf-8 -*-
import telebot, os, re
from telebot import types
from datetime import datetime
import pytz   # برای تایم‌زون‌ها

# ================== تنظیمات ==================
TOKEN   = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
# ============================================

HELP_TEXT = """
📖 لیست دستورات:

⏰ ساعت (با تاریخ و دو منطقه زمانی)
📊 آمار | 🆔 ایدی (با عکس پروفایل)
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
"""

# ========= سودوها =========
sudo_ids = {SUDO_ID}
def is_sudo(uid): return uid in sudo_ids

# ========= کمک‌تابع =========
def is_admin(chat_id, user_id):
    if is_sudo(user_id): return True
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator", "creator")
    except: return False

def cmd_text(m): return (getattr(m,"text",None) or getattr(m,"caption",None) or "").strip()

# ——— ذخیره گروه‌ها برای ارسال همگانی ———
joined_groups = set()
@bot.my_chat_member_handler()
def track_groups(upd):
    try:
        chat = upd.chat
        if chat and chat.type in ("group","supergroup"):
            joined_groups.add(chat.id)
    except: pass

# ========= دستورات پایه =========
@bot.message_handler(func=lambda m: cmd_text(m)=="راهنما") 
def help_cmd(m): bot.reply_to(m, HELP_TEXT)

@bot.message_handler(func=lambda m: cmd_text(m)=="ساعت")
def time_date_cmd(m):
    tz_eu = pytz.timezone("Europe/Berlin")   # اروپا
    tz_asia = pytz.timezone("Asia/Tehran")   # ایران
    now_eu = datetime.now(tz_eu).strftime("%H:%M:%S")
    now_asia = datetime.now(tz_asia).strftime("%H:%M:%S")
    today = datetime.now(tz_asia).strftime("%Y-%m-%d")
    bot.reply_to(m, f"📅 تاریخ: {today}\n⏰ اروپا: {now_eu}\n⏰ ایران: {now_asia}")

@bot.message_handler(func=lambda m: cmd_text(m)=="ایدی")
def id_cmd(m):
    try:
        photos = bot.get_user_profile_photos(m.from_user.id, limit=1)
        caption = f"🆔 شما: <code>{m.from_user.id}</code>\n🆔 گروه: <code>{m.chat.id}</code>"
        if photos.total_count > 0:
            file_id = photos.photos[0][-1].file_id
            bot.send_photo(m.chat.id, file_id, caption=caption)
        else:
            bot.reply_to(m, caption)
    except:
        bot.reply_to(m, f"🆔 شما: <code>{m.from_user.id}</code>\n🆔 گروه: <code>{m.chat.id}</code>")

@bot.message_handler(func=lambda m: cmd_text(m)=="آمار")
def stats(m):
    try: count=bot.get_chat_member_count(m.chat.id)
    except: count="نامشخص"
    bot.reply_to(m,f"📊 اعضای گروه: {count}")

# ========= خوشامد =========
welcome_enabled, welcome_texts, welcome_photos = {}, {}, {}
@bot.message_handler(content_types=['new_chat_members'])
def welcome(m):
    for u in m.new_chat_members:
        if not welcome_enabled.get(m.chat.id): continue
        name=(u.first_name or "")
        txt=welcome_texts.get(m.chat.id,"خوش آمدی 🌹").replace("{name}",name)
        if m.chat.id in welcome_photos: bot.send_photo(m.chat.id,welcome_photos[m.chat.id],caption=txt)
        else: bot.send_message(m.chat.id,txt)

@bot.message_handler(func=lambda m: cmd_text(m)=="خوشامد روشن")
def w_on(m): 
    if is_admin(m.chat.id,m.from_user.id): welcome_enabled[m.chat.id]=True; bot.reply_to(m,"✅ خوشامد روشن شد.")

@bot.message_handler(func=lambda m: cmd_text(m)=="خوشامد خاموش")
def w_off(m): 
    if is_admin(m.chat.id,m.from_user.id): welcome_enabled[m.chat.id]=False; bot.reply_to(m,"❌ خوشامد خاموش شد.")

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

# ========= بقیه کد (قفل‌ها، بن، سکوت، اخطار، مدیر، پن، پاکسازی، ارسال همگانی، سودو، لفت بده ...) =========
# 👇 این بخش همون کدی هست که دادی و من تغییری ندادم (فقط بالایی‌ها ویرایش شد)
# ========= قفل‌ها =========
# ========= بن / سکوت =========
# ========= اخطار =========
# ========= مدیر / حذف مدیر =========
# ========= پن =========
# ========= لیست =========
# ========= پاکسازی =========
# ========= ارسال همگانی =========
# ========= مدیریت سودو =========
# ========= لفت بده =========
# ========= جواب سودو =========

print("🤖 Bot is running...")
bot.infinity_polling()
