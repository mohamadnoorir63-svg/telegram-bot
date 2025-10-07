# -*- coding: utf-8 -*-
import os
import telebot

TOKEN   = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ================== کمک ==================
def is_admin(chat_id, user_id):
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator", "creator")
    except:
        return False

def cmd_text(m): return (getattr(m,"text",None) or "").strip()

# ================== بن ==================
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="بن")
def ban(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        bot.ban_chat_member(m.chat.id, m.reply_to_message.from_user.id)
        bot.reply_to(m, "🚫 کاربر بن شد")
    except Exception as e:
        bot.reply_to(m, f"❗ خطا: {e}")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف بن")
def unban(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        bot.unban_chat_member(m.chat.id, m.reply_to_message.from_user.id)
        bot.reply_to(m, "✅ بن حذف شد")
    except Exception as e:
        bot.reply_to(m, f"❗ خطا: {e}")

# ================== سکوت ==================
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="سکوت")
def mute(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        bot.restrict_chat_member(m.chat.id, m.reply_to_message.from_user.id, can_send_messages=False)
        bot.reply_to(m, "🔕 کاربر در سکوت قرار گرفت")
    except Exception as e:
        bot.reply_to(m, f"❗ خطا: {e}")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف سکوت")
def unmute(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        bot.restrict_chat_member(
            m.chat.id, m.reply_to_message.from_user.id,
            can_send_messages=True, can_send_media_messages=True,
            can_send_other_messages=True, can_add_web_page_previews=True
        )
        bot.reply_to(m, "🔊 سکوت حذف شد")
    except Exception as e:
        bot.reply_to(m, f"❗ خطا: {e}")

# ================== اخطار ==================
warnings = {}
MAX_WARNINGS = 3

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="اخطار")
def warn(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    warnings.setdefault(m.chat.id, {})
    warnings[m.chat.id][uid] = warnings[m.chat.id].get(uid, 0) + 1
    c = warnings[m.chat.id][uid]
    if c >= MAX_WARNINGS:
        try:
            bot.ban_chat_member(m.chat.id, uid)
            warnings[m.chat.id][uid] = 0
            bot.reply_to(m, "🚫 کاربر با ۳ اخطار بن شد")
        except Exception as e:
            bot.reply_to(m, f"❗ خطا: {e}")
    else:
        bot.reply_to(m, f"⚠️ اخطار {c}/{MAX_WARNINGS}")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف اخطار")
def reset_warn(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    warnings.get(m.chat.id, {}).pop(uid, None)
    bot.reply_to(m, "✅ اخطارها حذف شد")

# ================== پاکسازی ==================
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m)=="پاکسازی")
def clear_all(m):
    deleted = 0
    for i in range(1, 101):  # تا 100 پیام اخیر
        try:
            bot.delete_message(m.chat.id, m.message_id - i)
            deleted += 1
        except:
            continue
    bot.reply_to(m, f"🧹 {deleted} پیام پاک شد")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("حذف "))
def delete_n(m):
    try:
        n = int(cmd_text(m).split()[1])
        deleted = 0
        for i in range(1, n+1):
            try:
                bot.delete_message(m.chat.id, m.message_id - i)
                deleted += 1
            except:
                continue
        bot.reply_to(m, f"🗑 {deleted} پیام پاک شد")
    except:
        bot.reply_to(m, "❗ فرمت درست: حذف 10")# ================== قفل‌ها ==================
locks={k:{} for k in ["links","stickers","bots","photo","video","gif","file","music","voice","forward"]}
LOCK_MAP={"لینک":"links","استیکر":"stickers","ربات":"bots","عکس":"photo","ویدیو":"video",
          "گیف":"gif","فایل":"file","موزیک":"music","ویس":"voice","فوروارد":"forward"}

@bot.message_handler(func=lambda m: cmd_text(m).startswith("قفل "))
def lock(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    key_fa=cmd_text(m).replace("قفل ","",1)
    key=LOCK_MAP.get(key_fa)
    if key: locks[key][m.chat.id]=True; bot.reply_to(m,f"🔒 قفل {key_fa} فعال شد")

@bot.message_handler(func=lambda m: cmd_text(m).startswith("باز کردن "))
def unlock(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    key_fa=cmd_text(m).replace("باز کردن ","",1)
    key=LOCK_MAP.get(key_fa)
    if key: locks[key][m.chat.id]=False; bot.reply_to(m,f"🔓 قفل {key_fa} باز شد")

# enforce
@bot.message_handler(content_types=['text','photo','video','document','audio','voice','sticker','animation'])
def enforce(m):
    if is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id): return
    txt=m.text or ""
    try:
        if locks["links"].get(m.chat.id) and any(x in txt for x in ["http://","https://","t.me"]): bot.delete_message(m.chat.id,m.message_id)
        if locks["stickers"].get(m.chat.id) and m.sticker: bot.delete_message(m.chat.id,m.message_id)
        if locks["photo"].get(m.chat.id) and m.photo: bot.delete_message(m.chat.id,m.message_id)
        if locks["video"].get(m.chat.id) and m.video: bot.delete_message(m.chat.id,m.message_id)
        if locks["gif"].get(m.chat.id) and m.animation: bot.delete_message(m.chat.id,m.message_id)
        if locks["file"].get(m.chat.id) and m.document: bot.delete_message(m.chat.id,m.message_id)
        if locks["music"].get(m.chat.id) and m.audio: bot.delete_message(m.chat.id,m.message_id)
        if locks["voice"].get(m.chat.id) and m.voice: bot.delete_message(m.chat.id,m.message_id)
        if locks["forward"].get(m.chat.id) and (m.forward_from or m.forward_from_chat): bot.delete_message(m.chat.id,m.message_id)
    except: pass
print("🤖 Bot is running...")
bot.infinity_polling(skip_pending=True, timeout=30)
