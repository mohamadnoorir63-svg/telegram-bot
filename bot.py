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

⏰ ساعت | 🆔 ایدی | 📊 آمار | 🔗 لینک
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
❓ من کیم | ❓ این کیه (ریپلای)
🏷 لقب [متن] (ریپلای) | 🏷 لقب (ریپلای)
"""

# ========= سودو =========
sudo_ids = {SUDO_ID}
def is_sudo(uid): return uid in sudo_ids

def is_admin(chat_id, user_id):
    if is_sudo(user_id): return True
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator","creator")
    except: return False

def cmd_text(m): return (getattr(m,"text",None) or getattr(m,"caption",None) or "").strip()

# ========= ذخیره گروه‌ها =========
joined_groups=set()
@bot.my_chat_member_handler()
def track_groups(upd):
    try:
        chat=upd.chat
        if chat and chat.type in ("group","supergroup"): joined_groups.add(chat.id)
    except: pass

# ========= دستورات پایه =========
@bot.message_handler(func=lambda m: cmd_text(m)=="راهنما")
def help_cmd(m): bot.reply_to(m,HELP_TEXT)

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

# ========= لینک =========
@bot.message_handler(func=lambda m: cmd_text(m)=="لینک")
def send_link(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try:
        inv = bot.export_chat_invite_link(m.chat.id)
        bot.reply_to(m, f"🔗 لینک گروه:\n{inv}")
    except:
        bot.reply_to(m,"❗ نتونستم لینک بگیرم. مطمئن شو دسترسی ساخت لینک دارم.")

# ========= لقب و نقش =========
nicknames = {}

@bot.message_handler(func=lambda m: cmd_text(m)=="من کیم")
def who_am_i(m):
    role = "👤 عضو عادی"
    if is_sudo(m.from_user.id): role = "👑 سودو"
    elif is_admin(m.chat.id,m.from_user.id): role = "🛡 مدیر گروه"
    nick = nicknames.get((m.chat.id,m.from_user.id))
    if nick: role += f"\n🏷 لقب: {nick}"
    bot.reply_to(m, f"❓ تو: {role}")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="این کیه")
def who_is_he(m):
    u = m.reply_to_message.from_user
    role = "👤 عضو عادی"
    if is_sudo(u.id): role = "👑 سودو"
    elif is_admin(m.chat.id,u.id): role = "🛡 مدیر گروه"
    nick = nicknames.get((m.chat.id,u.id))
    if nick: role += f"\n🏷 لقب: {nick}"
    bot.reply_to(m, f"❓ این کاربر: {role}")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m).startswith("لقب "))
def set_nick(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    u = m.reply_to_message.from_user
    nick = cmd_text(m).replace("لقب ","",1).strip()
    if not nick: return bot.reply_to(m,"❗ لقبت خالیه.")
    nicknames[(m.chat.id,u.id)] = nick
    bot.reply_to(m,f"✅ لقب برای {u.first_name} ذخیره شد.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="لقب")
def show_nick(m):
    u = m.reply_to_message.from_user
    nick = nicknames.get((m.chat.id,u.id))
    if nick: bot.reply_to(m,f"🏷 لقب این کاربر: {nick}")
    else: bot.reply_to(m,"ℹ️ لقبی ثبت نشده.")

# ========= ادامه کدهای قبلی (خوشامد، قفل‌ها، بن، سکوت، اخطار، مدیر، پن، لیست، پاکسازی، ارسال همگانی، سودوها، لفت بده) =========
# (اینا همون بخش‌های آخرین بروزرسانی هستن که تو فرستادی بدون تغییر موندن)
# ========= RUN =========
print("🤖 Bot is running...")
bot.infinity_polling()
