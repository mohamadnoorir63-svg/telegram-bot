# -*- coding: utf-8 -*-
import telebot
from telebot import types
from datetime import datetime
import re

# ================== تنظیمات ==================
TOKEN   = "توکن_اینجا"
SUDO_ID = 123456789   # آیدی سودوی اولیه
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
# ============================================

HELP_TEXT = """
📖 لیست دستورات:

⏰ ساعت | 📅 تاریخ | 📊 آمار | 🆔 ایدی
🛠 وضعیت ربات
🎉 خوشامد روشن / خاموش
✍️ خوشامد متن [متن]
🖼 ثبت عکس (ریپلای به عکس)
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
🧹 پاکسازی              (۵۰ پیام)
🧹 پاکسازی 999         (۹۹۹ پیام)
🧹 پاکسازی 9999        (۹۹۹۹ پیام)
📢 ارسال                (فقط سودو؛ پیام بعدی به همه گروه‌ها)
➕ افزودن سودو [آیدی]
➖ حذف سودو [آیدی]
🚪 لفت بده              (فقط سودو)
"""

# ========= سودوها =========
sudo_ids = {SUDO_ID}

def is_sudo(uid:int)->bool:
    return uid in sudo_ids

# ========= کمک‌تابع‌ها =========
def is_admin(chat_id, user_id):
    if is_sudo(user_id): return True
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator", "creator")
    except: return False

def cmd_text(m): return (getattr(m,"text",None) or getattr(m,"caption",None) or "").strip()

# ——— ذخیره گروه‌ها برای «ارسال» ———
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
def time_cmd(m): bot.reply_to(m, f"⏰ ساعت: {datetime.now().strftime('%H:%M:%S')}")

@bot.message_handler(func=lambda m: cmd_text(m)=="تاریخ")
def date_cmd(m): bot.reply_to(m, f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d')}")

@bot.message_handler(func=lambda m: cmd_text(m)=="ایدی")
def id_cmd(m): bot.reply_to(m, f"🆔 آیدی شما: <code>{m.from_user.id}</code>\n🆔 آیدی گروه: <code>{m.chat.id}</code>")

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
        txt = welcome_texts.get(m.chat.id, "خوش آمدی 🌹").replace("{name}", u.first_name or "")
        if m.chat.id in welcome_photos:
            bot.send_photo(m.chat.id, welcome_photos[m.chat.id], caption=txt)
        else:
            bot.send_message(m.chat.id, txt)

@bot.message_handler(func=lambda m: cmd_text(m) == "خوشامد روشن")
def welcome_on(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    welcome_enabled[m.chat.id]=True
    bot.reply_to(m,"✅ خوشامد فعال شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "خوشامد خاموش")
def welcome_off(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    welcome_enabled[m.chat.id]=False
    bot.reply_to(m,"❌ خوشامد خاموش شد.")

@bot.message_handler(func=lambda m: m.text and m.text.startswith("خوشامد متن"))
def welcome_text(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    txt = m.text.replace("خوشامد متن","",1).strip()
    welcome_texts[m.chat.id]=txt
    bot.reply_to(m,"✍️ متن خوشامد ذخیره شد.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="ثبت عکس")
def save_photo(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    if not m.reply_to_message.photo: return
    welcome_photos[m.chat.id]=m.reply_to_message.photo[-1].file_id
    bot.reply_to(m,"🖼 عکس خوشامد ذخیره شد.")

# ========= قفل‌ها =========
locks = {k:{} for k in ["links","stickers","bots","tabchi","group","photo","video","gif","file","music","voice","forward"]}

LOCK_MAP = {
    "لینک": "links",
    "استیکر": "stickers",
    "ربات": "bots",
    "تبچی": "tabchi",
    "گروه": "group",
    "عکس": "photo",
    "ویدیو": "video",
    "گیف": "gif",
    "فایل": "file",
    "موزیک": "music",
    "ویس": "voice",
    "فوروارد": "forward",
}

@bot.message_handler(func=lambda m: m.text and (m.text.startswith("قفل ") or m.text.startswith("باز کردن ")))
def toggle_lock(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    t = m.text
    enable = t.startswith("قفل ")
    name = t.replace("قفل ","",1).replace("باز کردن ","",1).strip()
    key = LOCK_MAP.get(name)
    if not key: return
    if key=="group":
        try:
            bot.set_chat_permissions(m.chat.id, types.ChatPermissions(can_send_messages=not enable))
            locks[key][m.chat.id]=enable
            return bot.reply_to(m,"🔐 گروه قفل شد." if enable else "✅ گروه باز شد.")
        except: return bot.reply_to(m,"❗ دسترسی محدودسازی لازم است.")
    locks[key][m.chat.id]=enable
    bot.reply_to(m,f"{'🔒' if enable else '🔓'} {name} {'فعال شد' if enable else 'آزاد شد'}")

# بلاک لینک/فوروارد/مدیا
@bot.message_handler(content_types=['text','photo','video','document','audio','voice','sticker','animation'])
def guard(m):
    if locks["forward"].get(m.chat.id) and (m.forward_from or m.forward_from_chat or getattr(m,"forward_sender_name",None)):
        try: bot.delete_message(m.chat.id,m.message_id)
        except: pass
        return
    if locks["links"].get(m.chat.id) and not is_admin(m.chat.id,m.from_user.id):
        txt=(m.text or "").lower()
        if re.search(r"(t\.me|telegram\.me|telegram\.org|https?://)",txt):
            try: bot.delete_message(m.chat.id,m.message_id)
            except: pass
            return
    try:
        if locks["photo"].get(m.chat.id) and m.content_type=="photo": bot.delete_message(m.chat.id,m.message_id)
        if locks["video"].get(m.chat.id) and m.content_type=="video": bot.delete_message(m.chat.id,m.message_id)
        if locks["gif"].get(m.chat.id) and (m.content_type=="animation" or (m.document and getattr(m.document,"mime_type","")=="video/mp4")): bot.delete_message(m.chat.id,m.message_id)
        if locks["file"].get(m.chat.id) and m.content_type=="document": bot.delete_message(m.chat.id,m.message_id)
        if locks["music"].get(m.chat.id) and m.content_type=="audio": bot.delete_message(m.chat.id,m.message_id)
        if locks["voice"].get(m.chat.id) and m.content_type=="voice": bot.delete_message(m.chat.id,m.message_id)
        if locks["stickers"].get(m.chat.id) and m.content_type=="sticker": bot.delete_message(m.chat.id,m.message_id)
    except: pass
        print("🤖 Bot is running...")
bot.infinity_polling()
