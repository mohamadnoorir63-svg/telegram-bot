# -*- coding: utf-8 -*-
import telebot
from telebot import types
from datetime import datetime
import re

# ================== تنظیمات ==================
TOKEN   = "7462131830:AAEGzgbjETaf3eukzGHW613i4y61Cs7lzTE"
SUDO_ID = 7089376754  # آیدی سودو
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
# ============================================

HELP_TEXT = """
📖 لیست دستورات:

⏰ ساعت | 📅 تاریخ | 📊 آمار | 🆔 ایدی
🔒 قفل لینک / باز کردن لینک
🧷 قفل استیکر / باز کردن استیکر
🤖 قفل ربات / باز کردن ربات
🚫 قفل تبچی / باز کردن تبچی
🔐 قفل گروه / باز کردن گروه
🚫 بن / ✅ حذف بن (ریپلای)
🔕 سکوت / 🔊 حذف سکوت (ریپلای)
⚠️ اخطار (ریپلای)
👑 مدیر / ❌ حذف مدیر (ریپلای)
📌 پن / ❌ حذف پن (ریپلای)
📋 لیست مدیران گروه
📋 لیست مدیران ربات
🎉 خوشامد روشن / خاموش
✍️ خوشامد متن [متن دلخواه]
🖼 ثبت عکس (ریپلای روی عکس و بفرست: ثبت عکس)
🧹 پاکسازی (حذف ۵۰ پیام آخر)
🧹 پاکسازی [تعداد]
📢 ارسال (فقط سودو)
🛠 وضعیت ربات
🎨 فونت [کلمه]
🚪 لفت بده (فقط سودو)
"""

# ذخیره گروه‌ها
joined_groups = set()

@bot.my_chat_member_handler()
def track_groups(upd):
    if upd.chat and upd.chat.type in ("group", "supergroup"):
        joined_groups.add(upd.chat.id)

# کمک‌تابع چک ادمین
def is_admin(chat_id, user_id):
    if user_id == SUDO_ID: return True
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator","creator")
    except: return False

# ========= دستورات پایه =========
@bot.message_handler(func=lambda m: m.text=="راهنما")
def help_cmd(m): bot.reply_to(m, HELP_TEXT)

@bot.message_handler(func=lambda m: m.text=="ساعت")
def time_cmd(m): bot.reply_to(m, f"⏰ ساعت: {datetime.now().strftime('%H:%M:%S')}")

@bot.message_handler(func=lambda m: m.text=="تاریخ")
def date_cmd(m): bot.reply_to(m, f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d')}")

@bot.message_handler(func=lambda m: m.text=="ایدی")
def id_cmd(m): bot.reply_to(m, f"🆔 آیدی شما: <code>{m.from_user.id}</code>\n🆔 آیدی گروه: <code>{m.chat.id}</code>")

@bot.message_handler(func=lambda m: m.text=="آمار")
def stats(m):
    try: count = bot.get_chat_member_count(m.chat.id)
    except: count = "نامشخص"
    bot.reply_to(m, f"📊 اعضای گروه: {count}")

# ========= اخطار =========
warnings = {}
@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="اخطار")
def warn_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    warnings.setdefault(m.chat.id, {})
    warnings[m.chat.id][uid] = warnings[m.chat.id].get(uid, 0) + 1
    count = warnings[m.chat.id][uid]
    if count >= 3:
        try:
            bot.ban_chat_member(m.chat.id, uid)
            bot.reply_to(m, f"🚫 کاربر {uid} به دلیل دریافت ۳ اخطار بن شد.")
        except:
            bot.reply_to(m, "❗ نتوانستم بن کنم.")
    else:
        bot.reply_to(m, f"⚠️ اخطار {count}/3 به کاربر داده شد.")

# ========= پاکسازی =========
@bot.message_handler(func=lambda m: m.text=="پاکسازی")
def clear_50(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    for i in range(m.message_id-1, m.message_id-51, -1):
        try: bot.delete_message(m.chat.id, i)
        except: pass
    bot.reply_to(m, "🧹 ۵۰ پیام آخر پاک شد.")

@bot.message_handler(func=lambda m: m.text and m.text.startswith("پاکسازی "))
def clear_custom(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        n = int(m.text.split()[1])
        for i in range(m.message_id-1, m.message_id-n-1, -1):
            try: bot.delete_message(m.chat.id, i)
            except: pass
        bot.reply_to(m, f"🧹 {n} پیام آخر پاک شد.")
    except: pass

# ========= فونت‌ساز =========
fonts_fa = [
    "مَِــَِ{}َِــَِ",
    "ۘۘمـ ۘۘحـ ۘۘ{}",
    "مـــ{}ّ",
    "مـ﹏ـ{}﹏ـد",
    "مـ෴ِْ{}෴ِْد"
]

fonts_en = [
    "ⓜⓞ{}",
    "мσ{}",
    "𝐌𝐎{}",
    "𝑴𝑶{}",
    "𝕸𝕺{}",
    "𝔐𝔒{}",
    "𝗠𝗢{}",
    "ＭＯ{}",
    "мø{}",
    "🅼🅾️{}"
]

@bot.message_handler(func=lambda m: m.text and m.text.startswith("فونت "))
def font_cmd(m):
    word = m.text.replace("فونت","",1).strip()
    if not word: return
    results = []
    for f in fonts_fa[:5]:
        results.append(f.replace("{}", word))
    for f in fonts_en[:5]:
        results.append(f.replace("{}", word.upper()))
    bot.reply_to(m, "🎨 نمونه فونت‌ها:\n" + "\n".join(results))

# ========= ضد لینک + جواب سودو =========
@bot.message_handler(content_types=['text'])
def text_handler(m):
    if m.from_user.id==SUDO_ID and m.text.strip()=="ربات":
        return bot.reply_to(m,"جانم سودو 👑")
    if re.search(r"(t\.me|http)", (m.text or "").lower()):
        try: bot.delete_message(m.chat.id,m.message_id)
        except: pass

# ========= RUN =========
print("🤖 Bot is running...")
bot.infinity_polling()
