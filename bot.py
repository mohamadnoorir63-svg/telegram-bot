# -*- coding: utf-8 -*-
import telebot, re
from datetime import datetime

TOKEN   = "7462131830:AAEGzgbjETaf3eukzGHW613i4y61Cs7lzTE"
SUDO_ID = 7089376754
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# حافظه ساده
locks = {"links":{}, "stickers":{}, "bots":{}, "tabchi":{}}
welcome_enabled, welcome_texts, welcome_photos = {}, {}, {}

HELP_TEXT = """
📖 لیست دستورات:

⏰ ساعت | 📅 تاریخ | 📊 آمار | 🆔 ایدی
🔒 قفل لینک / باز کردن لینک
🧷 قفل استیکر / باز کردن استیکر
📛 قفل تبچی / باز کردن تبچی
🤖 قفل ربات / باز کردن ربات
🎉 خوشامد روشن / خاموش
✍️ خوشامد متن <متن>
🖼 ثبت عکس (ریپلای روی عکس و بفرست ثبت عکس)
🚪 لفت بده (فقط سودو)
"""

# ===== راهنما و پایه =====
@bot.message_handler(func=lambda m: m.text=="راهنما")
def help_cmd(m): bot.reply_to(m, HELP_TEXT)

@bot.message_handler(func=lambda m: m.text=="ساعت")
def time_cmd(m): bot.reply_to(m, f"⏰ {datetime.now().strftime('%H:%M:%S')}")

@bot.message_handler(func=lambda m: m.text=="تاریخ")
def date_cmd(m): bot.reply_to(m, f"📅 {datetime.now().strftime('%Y-%m-%d')}")

@bot.message_handler(func=lambda m: m.text=="آمار")
def stats_cmd(m):
    try: count = bot.get_chat_member_count(m.chat.id)
    except: count = "نامشخص"
    bot.reply_to(m, f"📊 اعضای گروه: {count}")

@bot.message_handler(func=lambda m: m.text=="ایدی")
def id_cmd(m):
    bot.reply_to(m, f"🆔 شما: <code>{m.from_user.id}</code>\n🆔 گروه: <code>{m.chat.id}</code>")

# ===== خوشامد =====
@bot.message_handler(content_types=['new_chat_members'])
def new_member(m):
    # قفل ربات
    if locks["bots"].get(m.chat.id):
        for u in m.new_chat_members:
            if u.is_bot:
                try:
                    bot.kick_chat_member(m.chat.id,u.id)
                    bot.send_message(m.chat.id,"🤖 ربات ممنوعه و حذف شد.")
                except: pass
                return
    # خوشامد
    if welcome_enabled.get(m.chat.id):
        for u in m.new_chat_members:
            name = u.first_name
            txt = welcome_texts.get(m.chat.id,"خوش آمدی 🌹").replace("{name}",name)
            if m.chat.id in welcome_photos:
                bot.send_photo(m.chat.id, welcome_photos[m.chat.id], caption=txt)
            else:
                bot.send_message(m.chat.id, txt)

@bot.message_handler(func=lambda m: m.text=="خوشامد روشن")
def w_on(m): welcome_enabled[m.chat.id]=True; bot.reply_to(m,"✅ خوشامد روشن شد.")

@bot.message_handler(func=lambda m: m.text=="خوشامد خاموش")
def w_off(m): welcome_enabled[m.chat.id]=False; bot.reply_to(m,"❌ خوشامد خاموش شد.")

@bot.message_handler(func=lambda m: m.text and m.text.startswith("خوشامد متن"))
def w_text(m):
    txt = m.text.replace("خوشامد متن","",1).strip()
    welcome_texts[m.chat.id]=txt
    bot.reply_to(m,"✍️ متن خوشامد ذخیره شد.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="ثبت عکس")
def w_photo(m):
    if not m.reply_to_message.photo: return
    welcome_photos[m.chat.id] = m.reply_to_message.photo[-1].file_id
    bot.reply_to(m,"🖼 عکس خوشامد ذخیره شد.")

# ===== قفل لینک =====
@bot.message_handler(func=lambda m: m.text=="قفل لینک")
def l1(m): locks["links"][m.chat.id]=True; bot.reply_to(m,"🔒 لینک‌ها قفل شدند.")

@bot.message_handler(func=lambda m: m.text=="باز کردن لینک")
def l2(m): locks["links"][m.chat.id]=False; bot.reply_to(m,"🔓 لینک‌ها آزاد شدند.")

# ===== قفل استیکر =====
@bot.message_handler(func=lambda m: m.text=="قفل استیکر")
def s1(m): locks["stickers"][m.chat.id]=True; bot.reply_to(m,"🧷 استیکرها قفل شدند.")

@bot.message_handler(func=lambda m: m.text=="باز کردن استیکر")
def s2(m): locks["stickers"][m.chat.id]=False; bot.reply_to(m,"🧷 استیکرها آزاد شدند.")

# ===== قفل تبچی (کاربر تبلیغی) =====
@bot.message_handler(func=lambda m: m.text=="قفل تبچی")
def t1(m): locks["tabchi"][m.chat.id]=True; bot.reply_to(m,"📛 تبچی قفل شد.")

@bot.message_handler(func=lambda m: m.text=="باز کردن تبچی")
def t2(m): locks["tabchi"][m.chat.id]=False; bot.reply_to(m,"📛 تبچی آزاد شد.")

# ===== قفل ربات =====
@bot.message_handler(func=lambda m: m.text=="قفل ربات")
def b1(m): locks["bots"][m.chat.id]=True; bot.reply_to(m,"🤖 ربات‌ها قفل شدند.")

@bot.message_handler(func=lambda m: m.text=="باز کردن ربات")
def b2(m): locks["bots"][m.chat.id]=False; bot.reply_to(m,"🤖 ربات‌ها آزاد شدند.")

# ===== حذف محتوای ممنوع =====
@bot.message_handler(content_types=['text','sticker'])
def cleaner(m):
    if locks["links"].
