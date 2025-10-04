# -*- coding: utf-8 -*-
import telebot, re
from telebot import types
from datetime import datetime

# ==================
TOKEN = "7462131830:AAEGzgbjETaf3eukzGHW613i4y61Cs7lzTE"
SUDO_ID = 7089376754  # آیدی عددی شما
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
# ==================

HELP_TEXT = """
📖 لیست دستورات:

⏰ ساعت | 📅 تاریخ | 📊 آمار | 🆔 ایدی
🔒 قفل لینک / باز کردن لینک
🧷 قفل استیکر / باز کردن استیکر
📛 قفل تبچی / باز کردن تبچی
🤖 قفل ربات / باز کردن ربات
🚫 بن / ✅ حذف بن (ریپلای)
🔕 سکوت / 🔊 حذف سکوت (ریپلای)
👑 مدیر / ❌ حذف مدیر (ریپلای)
🎉 خوشامد روشن / خاموش
✍️ خوشامد متن <متن>
🖼 ثبت عکس (ریپلای روی عکس و بفرست ثبت عکس)
🚪 لفت بده (فقط سودو)
"""

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

# ========= خوشامدگویی =========
welcome_enabled, welcome_texts, welcome_photos = {}, {}, {}

@bot.message_handler(content_types=['new_chat_members'])
def welcome(m):
    if not welcome_enabled.get(m.chat.id): return
    for u in m.new_chat_members:
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

# ========= لفت بده =========
@bot.message_handler(func=lambda m: m.text=="لفت بده")
def leave_cmd(m):
    if m.from_user.id!=SUDO_ID: return
    bot.send_message(m.chat.id,"به دستور سودو خارج می‌شوم 👋")
    bot.leave_chat(m.chat.id)

# ========= قفل لینک =========
lock_links, lock_stickers, lock_tabchi, lock_bots = {}, {}, {}, {}

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
    if lock_links.get(m.chat.id) and m.from_user.id!=SUDO_ID:
        if re.search(r"(t\.me|http)", m.text.lower()):
            try: bot.delete_message(m.chat.id, m.message_id)
            except: pass

# ========= قفل استیکر =========
@bot.message_handler(func=lambda m: m.text=="قفل استیکر")
def lock_sticker_cmd(m):
    lock_stickers[m.chat.id]=True
    bot.reply_to(m,"🧷 استیکرها قفل شدند.")

@bot.message_handler(func=lambda m: m.text=="باز کردن استیکر")
def unlock_sticker_cmd(m):
    lock_stickers[m.chat.id]=False
    bot.reply_to(m,"🧷 استیکرها آزاد شدند.")

@bot.message_handler(content_types=['sticker'])
def anti_sticker(m):
    if lock_stickers.get(m.chat.id) and m.from_user.id!=SUDO_ID:
        try: bot.delete_message(m.chat.id, m.message_id)
        except: pass

# ========= قفل تبچی =========
@bot.message_handler(content_types=['new_chat_members'])
def anti_tabchi(m):
    if lock_tabchi.get(m.chat.id):
        for u in m.new_chat_members:
            if u.username and ("bot" not in u.username.lower()):
                if "t.me" in u.username.lower() or "spam" in u.username.lower():
                    try:
                        bot.kick_chat_member(m.chat.id,u.id)
                        bot.send_message(m.chat.id,f"🚫 کاربر {u.first_name} به خاطر تبچی حذف شد.")
                    except: pass

@bot.message_handler(func=lambda m: m.text=="قفل تبچی")
def lock_tabchi_cmd(m):
    lock_tabchi[m.chat.id]=True
    bot.reply_to(m,"📛 تبچی قفل شد.")

@bot.message_handler(func=lambda m: m.text=="باز کردن تبچی")
def unlock_tabchi_cmd(m):
    lock_tabchi[m.chat.id]=False
    bot.reply_to(m,"📛 تبچی آزاد شد.")

# ========= قفل ربات =========
@bot.message_handler(content_types=['new_chat_members'])
def anti_bot(m):
    if lock_bots.get(m.chat.id):
        for u in m.new_chat_members:
            if u.is_bot:
                try:
                    bot.kick_chat_member(m.chat.id,u.id)
                    bot.send_message(m.chat.id,"🤖 ربات ممنوعه و حذف شد.")
                except: pass

@bot.message_handler(func=lambda m: m.text=="قفل ربات")
def lock_bots_cmd(m):
    lock_bots[m.chat.id]=True
    bot.reply_to(m,"🤖 ربات‌ها قفل شدند.")

@bot.message_handler(func=lambda m: m.text=="باز کردن ربات")
def unlock_bots_cmd(m):
    lock_bots[m.chat.id]=False
    bot.reply_to(m,"🤖 ربات‌ها آزاد شدند.")

# ========= RUN =========
print("🤖 Bot is running...")
bot.infinity_polling()
