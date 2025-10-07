# -*- coding: utf-8 -*-
import os
import telebot

# ====== تنظیمات ======
TOKEN   = os.environ.get("BOT_TOKEN")   # توکن ربات
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))  # آیدی سودو

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
sudo_ids = {SUDO_ID}

# ====== کمکی ======
def cmd_text(m):
    return (getattr(m,"text",None) or "").strip()

def is_sudo(uid):
    return uid in sudo_ids

def is_admin(chat_id, user_id):
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator","creator")
    except:
        return False

# ====== قفل‌ها ======
locks={k:{} for k in ["links","stickers","bots","photo","video","gif","file","music","voice","forward"]}
LOCK_MAP={
    "لینک":"links",
    "استیکر":"stickers",
    "ربات":"bots",
    "عکس":"photo",
    "ویدیو":"video",
    "گیف":"gif",
    "فایل":"file",
    "موزیک":"music",
    "ویس":"voice",
    "فوروارد":"forward"
}

# نمایش پنل
@bot.message_handler(func=lambda m: cmd_text(m)=="پنل")
def locks_panel(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)):
        return
    kb=telebot.types.InlineKeyboardMarkup(row_width=2)
    for name,key in LOCK_MAP.items():
        st="🔒" if locks[key].get(m.chat.id) else "🔓"
        kb.add(telebot.types.InlineKeyboardButton(f"{st} {name}",callback_data=f"toggle:{key}:{m.chat.id}"))
    kb.add(telebot.types.InlineKeyboardButton("❌ بستن",callback_data=f"close:{m.chat.id}"))
    bot.reply_to(m,"🛠 پنل مدیریت قفل‌ها:",reply_markup=kb)

# تغییر وضعیت
@bot.callback_query_handler(func=lambda c: c.data.startswith("toggle:"))
def cb_toggle(c):
    _,key,chat_id=c.data.split(":")
    chat_id=int(chat_id)
    if not (is_admin(chat_id,c.from_user.id) or is_sudo(c.from_user.id)):
        return
    locks[key][chat_id]=not locks[key].get(chat_id,False)
    st="فعال" if locks[key][chat_id] else "غیرفعال"
    bot.answer_callback_query(c.id,f"✅ قفل {st} شد")

# بستن پنل
@bot.callback_query_handler(func=lambda c: c.data.startswith("close:"))
def cb_close(c):
    try:
        bot.delete_message(c.message.chat.id,c.message.message_id)
    except: pass
    bot.answer_callback_query(c.id,"❌ پنل بسته شد")

# enforce قفل‌ها
@bot.message_handler(content_types=['text','photo','video','document','audio','voice','sticker','animation'])
def enforce(m):
    if is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id):
        return
    txt=m.text or ""
    try:
        if locks["links"].get(m.chat.id) and any(x in txt for x in ["http://","https://","t.me"]):
            bot.delete_message(m.chat.id,m.message_id)
        if locks["stickers"].get(m.chat.id) and m.sticker:
            bot.delete_message(m.chat.id,m.message_id)
        if locks["photo"].get(m.chat.id) and m.photo:
            bot.delete_message(m.chat.id,m.message_id)
        if locks["video"].get(m.chat.id) and m.video:
            bot.delete_message(m.chat.id,m.message_id)
        if locks["gif"].get(m.chat.id) and m.animation:
            bot.delete_message(m.chat.id,m.message_id)
        if locks["file"].get(m.chat.id) and m.document:
            bot.delete_message(m.chat.id,m.message_id)
        if locks["music"].get(m.chat.id) and m.audio:
            bot.delete_message(m.chat.id,m.message_id)
        if locks["voice"].get(m.chat.id) and m.voice:
            bot.delete_message(m.chat.id,m.message_id)
        if locks["forward"].get(m.chat.id) and (m.forward_from or m.forward_from_chat):
            bot.delete_message(m.chat.id,m.message_id)
    except: pass

# ====== اجرا ======
print("🤖 Bot is running...")
bot.infinity_polling(skip_pending=True,timeout=20)
