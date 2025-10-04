# -*- coding: utf-8 -*-
import telebot, re
from telebot import types
from datetime import datetime

# ==================
TOKEN = "7462131830:AAEGzgbjETaf3eukzGHW613i4y61Cs7lzTE"   # توکن
SUDO_ID = 7089376754  # آیدی سودو
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
# ==================

# حافظه ساده
welcome_enabled = {}
welcome_texts = {}
welcome_photos = {}
lock_links = {}
lock_stickers = {}
lock_bots = {}
lock_tabchi = {}
muted_users = {}
banned_users = {}

# ========= خوشامدگویی =========
@bot.message_handler(content_types=['new_chat_members'])
def welcome(m):
   # سکوت
@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="سکوت")
def mute_user(m):
    if not m.reply_to_message: return
    try:
        bot.restrict_chat_member(
            m.chat.id,
            m.reply_to_message.from_user.id,
            permissions=telebot.types.ChatPermissions(can_send_messages=False)
        )
        bot.reply_to(m, "🔇 کاربر در سکوت قرار گرفت.")
    except Exception as e:
        bot.reply_to(m, f"⚠️ خطا: {e}")

# حذف سکوت
@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="حذف سکوت")
def unmute_user(m):
    if not m.reply_to_message: return
    try:
        bot.restrict_chat_member(
            m.chat.id,
            m.reply_to_message.from_user.id,
            permissions=telebot.types.ChatPermissions(can_send_messages=True,
                                                      can_send_media_messages=True,
                                                      can_send_other_messages=True,
                                                      can_add_web_page_previews=True)
        )
        bot.reply_to(m, "🔊 سکوت کاربر برداشته شد.")
    except Exception as e:
        bot.reply_to(m, f"⚠️ خطا: {e}")

# بن
@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="بن")
def ban_user(m):
    if not m.reply_to_message: return
    try:
        bot.ban_chat_member(m.chat.id, m.reply_to_message.from_user.id)
        bot.reply_to(m, "🚫 کاربر بن شد.")
    except Exception as e:
        bot.reply_to(m, f"⚠️ خطا: {e}")

# حذف بن
@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="حذف بن")
def unban_user(m):
    if not m.reply_to_message: return
    try:
        bot.unban_chat_member(m.chat.id, m.reply_to_message.from_user.id)
        bot.reply_to(m, "✅ بن کاربر برداشته شد.")
    except Exception as e:
        bot.reply_to(m, f"⚠️ خطا: {e}") if not welcome_enabled.get(m.chat.id): return
    for u in m.new_chat_members:
        # قفل ربات
        if lock_bots.get(m.chat.id) and u.is_bot:
            try: bot.kick_chat_member(m.chat.id, u.id)
            except: pass
            continue
        # قفل تبچی (یوزرهایی که اسمشون tabchi دارن)
        if lock_tabchi.get(m.chat.id) and "tabchi" in (u.username or "").lower():
            try: bot.kick_chat_member(m.chat.id, u.id)
            except: pass
            continue

        name = u.first_name
        txt = welcome_texts.get(m.chat.id, "خوش آمدی 🌹").replace("{name}", name)
        if m.chat.id in welcome_photos:
            bot.send_photo(m.chat.id, welcome_photos[m.chat.id], caption=txt)
        else:
            bot.send_message(m.chat.id, txt)

@bot.message_handler(func=lambda m: m.text=="خوشامد روشن")
def welcome_on(m):
    welcome_enabled[m.chat.id]=True
    bot.reply_to(m, "✅ خوشامد فعال شد.")

@bot.message_handler(func=lambda m: m.text=="خوشامد خاموش")
def welcome_off(m):
    welcome_enabled[m.chat.id]=False
    bot.reply_to(m, "❌ خوشامد خاموش شد.")

@bot.message_handler(func=lambda m: m.text and m.text.startswith("خوشامد متن"))
def welcome_text(m):
    txt = m.text.replace("خوشامد متن","",1).strip()
    welcome_texts[m.chat.id]=txt
    bot.reply_to(m, "✍️ متن خوشامد ذخیره شد.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="ثبت عکس")
def save_photo(m):
    if not m.reply_to_message.photo: return
    welcome_photos[m.chat.id] = m.reply_to_message.photo[-1].file_id
    bot.reply_to(m, "🖼 عکس خوشامد ذخیره شد.")

# ========= دستورات پایه =========
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

# ========= قفل لینک =========
@bot.message_handler(func=lambda m: m.text=="قفل لینک")
def lock_links_cmd(m):
    lock_links[m.chat.id]=True
    bot.reply_to(m,"🔒 لینک‌ها قفل شدند.")

@bot.message_handler(func=lambda m: m.text=="باز کردن لینک")
def unlock_links_cmd(m):
    lock_links[m.chat.id]=False
    bot.reply_to(m,"🔓 لینک‌ها آزاد شدند.")

@bot.message_handler(content_types=['text'])
def anti_links(m):
    if lock_links.get(m.chat.id) and not m.from_user.id==SUDO_ID:
        if re.search(r"(t\.me|http)", m.text.lower()):
            try: bot.delete_message(m.chat.id, m.message_id)
            except: pass

# ========= قفل استیکر =========
@bot.message_handler(func=lambda m: m.text=="قفل استیکر")
def lock_sticker(m):
    lock_stickers[m.chat.id]=True
    bot.reply_to(m,"🔒 استیکرها قفل شدند.")

@bot.message_handler(func=lambda m: m.text=="باز کردن استیکر")
def unlock_sticker(m):
    lock_stickers[m.chat.id]=False
    bot.reply_to(m,"🔓 استیکرها آزاد شدند.")

@bot.message_handler(content_types=['sticker'])
def anti_sticker(m):
    if lock_stickers.get(m.chat.id) and not m.from_user.id==SUDO_ID:
        try: bot.delete_message(m.chat.id, m.message_id)
        except: pass

# ========= قفل ربات =========
@bot.message_handler(func=lambda m: m.text=="قفل ربات")
def lock_bots_cmd(m):
    lock_bots[m.chat.id]=True
    bot.reply_to(m,"🤖 ربات‌ها قفل شدند.")

@bot.message_handler(func=lambda m: m.text=="باز کردن ربات")
def unlock_bots_cmd(m):
    lock_bots[m.chat.id]=False
    bot.reply_to(m,"🤖 ربات‌ها آزاد شدند.")

# ========= قفل تبچی =========
@bot.message_handler(func=lambda m: m.text=="قفل تبچی")
def lock_tabchi_cmd(m):
    lock_tabchi[m.chat.id]=True
    bot.reply_to(m,"🚫 تبچی‌ها قفل شدند.")

@bot.message_handler(func=lambda m: m.text=="باز کردن تبچی")
def unlock_tabchi_cmd(m):
    lock_tabchi[m.chat.id]=False
    bot.reply_to(m,"🚫 تبچی‌ها آزاد شدند.")

# ========= سکوت / بن =========
@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="سکوت")
def mute_user(m):
    uid = m.reply_to_message.from_user.id
    muted_users.setdefault(m.chat.id, set()).add(uid)
    bot.reply_to(m,"🔇 کاربر در سکوت قرار گرفت.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="حذف سکوت")
def unmute_user(m):
    uid = m.reply_to_message.from_user.id
    muted_users.setdefault(m.chat.id, set()).discard(uid)
    bot.reply_to(m,"🔊 سکوت کاربر برداشته شد.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="بن")
def ban_user(m):
    uid = m.reply_to_message.from_user.id
    try:
        bot.kick_chat_member(m.chat.id, uid)
        banned_users.setdefault(m.chat.id, set()).add(uid)
        bot.reply_to(m,"⛔ کاربر بن شد.")
    except: pass

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="حذف بن")
def unban_user(m):
    uid = m.reply_to_message.from_user.id
    try:
        bot.unban_chat_member(m.chat.id, uid)
        banned_users.setdefault(m.chat.id, set()).discard(uid)
        bot.reply_to(m,"✅ کاربر آنبن شد.")
    except: pass

# جلوگیری از پیام سکوتی‌ها
@bot.message_handler(func=lambda m: True, content_types=['text','photo','video','sticker'])
def check_muted(m):
    if m.chat.id in muted_users and m.from_user.id in muted_users[m.chat.id]:
        try: bot.delete_message(m.chat.id, m.message_id)
        except: pass

# ========= لفت بده =========
@bot.message_handler(func=lambda m: m.text=="لفت بده")
def leave_cmd(m):
    if m.from_user.id!=SUDO_ID: return
    bot.send_message(m.chat.id,"به دستور سودو خارج می‌شوم 👋")
    bot.leave_chat(m.chat.id)

# ========= RUN =========
print("🤖 Bot is running...")
bot.infinity_polling()
