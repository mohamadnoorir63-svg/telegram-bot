# -*- coding: utf-8 -*-
import os, re
import telebot
from datetime import datetime

# توکن را از Config Vars هم می‌خوانیم (اگر ست شده باشد)
TOKEN   = os.getenv("BOT_TOKEN", "7462131830:AAEGzgbjETaf3eukzGHW613i4y61Cs7lzTE")
SUDO_ID = 7089376754

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# حافظه ساده برای هر گروه
locks = {"links":{}, "stickers":{}, "bots":{}, "tabchi":{}}
welcome_enabled, welcome_texts, welcome_photos = {}, {}, {}

HELP_TEXT = (
"📖 لیست دستورات:\n\n"
"⏰ ساعت | 📅 تاریخ | 📊 آمار | 🆔 ایدی\n"
"🔒 قفل لینک / باز کردن لینک\n"
"🧷 قفل استیکر / باز کردن استیکر\n"
"📛 قفل تبچی / باز کردن تبچی\n"
"🤖 قفل ربات / باز کردن ربات\n"
"🎉 خوشامد روشن / خوشامد خاموش\n"
"✍️ خوشامد متن <متن>\n"
"🖼 ثبت عکس (روی عکس ریپلای کن و بفرست: ثبت عکس)\n"
"🚪 لفت بده (فقط سودو)\n"
)

# ===== دستورات پایه
@bot.message_handler(func=lambda m: m.text=="راهنما")
def help_cmd(m): bot.reply_to(m, HELP_TEXT)

@bot.message_handler(func=lambda m: m.text=="ساعت")
def time_cmd(m): bot.reply_to(m, "⏰ " + datetime.now().strftime("%H:%M:%S"))

@bot.message_handler(func=lambda m: m.text=="تاریخ")
def date_cmd(m): bot.reply_to(m, "📅 " + datetime.now().strftime("%Y-%m-%d"))

@bot.message_handler(func=lambda m: m.text=="آمار")
def stats_cmd(m):
    try: count = bot.get_chat_member_count(m.chat.id)
    except: count = "نامشخص"
    bot.reply_to(m, f"📊 اعضای گروه: {count}")

@bot.message_handler(func=lambda m: m.text=="ایدی")
def id_cmd(m):
    bot.reply_to(m, f"🆔 شما: <code>{m.from_user.id}</code>\n🆔 گروه: <code>{m.chat.id}</code>")

# ===== خوشامد + قفل ربات در یک هندلر new_chat_members
@bot.message_handler(content_types=['new_chat_members'])
def new_member(m):
    # قفل ربات
    if locks["bots"].get(m.chat.id):
        for u in m.new_chat_members:
            if u.is_bot:
                try:
                    bot.kick_chat_member(m.chat.id, u.id)
                    bot.send_message(m.chat.id, "🤖 افزودن ربات ممنوع است و حذف شد.")
                except: pass
                return
    # خوشامد
    if welcome_enabled.get(m.chat.id):
        for u in m.new_chat_members:
            name = (u.first_name or "")
            txt = welcome_texts.get(m.chat.id, "خوش آمدی 🌹").replace("{name}", name)
            if m.chat.id in welcome_photos:
                bot.send_photo(m.chat.id, welcome_photos[m.chat.id], caption=txt)
            else:
                bot.send_message(m.chat.id, txt)

@bot.message_handler(func=lambda m: m.text=="خوشامد روشن")
def w_on(m): welcome_enabled[m.chat.id]=True; bot.reply_to(m, "✅ خوشامد روشن شد.")

@bot.message_handler(func=lambda m: m.text=="خوشامد خاموش")
def w_off(m): welcome_enabled[m.chat.id]=False; bot.reply_to(m, "❌ خوشامد خاموش شد.")

@bot.message_handler(func=lambda m: m.text and m.text.startswith("خوشامد متن"))
def w_text(m):
    txt = m.text.replace("خوشامد متن","",1).strip()
    if not txt: return bot.reply_to(m, "نمونه: خوشامد متن خوش آمدی {name} 🌹")
    welcome_texts[m.chat.id]=txt
    bot.reply_to(m, "✍️ متن خوشامد ذخیره شد.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="ثبت عکس")
def w_photo(m):
    if not m.reply_to_message.photo: return
    welcome_photos[m.chat.id] = m.reply_to_message.photo[-1].file_id
    bot.reply_to(m, "🖼 عکس خوشامد ذخیره شد.")

# ===== قفل‌ها
@bot.message_handler(func=lambda m: m.text=="قفل لینک")
def lock_links_on(m): locks["links"][m.chat.id]=True;  bot.reply_to(m, "🔒 لینک‌ها قفل شدند.")
@bot.message_handler(func=lambda m: m.text=="باز کردن لینک")
def lock_links_off(m): locks["links"][m.chat.id]=False; bot.reply_to(m, "🔓 لینک‌ها آزاد شدند.")

@bot.message_handler(func=lambda m: m.text=="قفل استیکر")
def lock_stickers_on(m): locks["stickers"][m.chat.id]=True;  bot.reply_to(m, "🧷 استیکرها قفل شدند.")
@bot.message_handler(func=lambda m: m.text=="باز کردن استیکر")
def lock_stickers_off(m): locks["stickers"][m.chat.id]=False; bot.reply_to(m, "🧷 استیکرها آزاد شدند.")

@bot.message_handler(func=lambda m: m.text=="قفل تبچی")
def lock_tabchi_on(m): locks["tabchi"][m.chat.id]=True;  bot.reply_to(m, "📛 تبچی قفل شد.")
@bot.message_handler(func=lambda m: m.text=="باز کردن تبچی")
def lock_tabchi_off(m): locks["tabchi"][m.chat.id]=False; bot.reply_to(m, "📛 تبچی آزاد شد.")

@bot.message_handler(func=lambda m: m.text=="قفل ربات")
def lock_bots_on(m): locks["bots"][m.chat.id]=True;  bot.reply_to(m, "🤖 ربات‌ها قفل شدند.")
@bot.message_handler(func=lambda m: m.text=="باز کردن ربات")
def lock_bots_off(m): locks["bots"][m.chat.id]=False; bot.reply_to(m, "🤖 ربات‌ها آزاد شدند.")

# ===== پاک‌سازی محتوای ممنوع
@bot.message_handler(content_types=['text','sticker'])
def cleaner(m):
    if m.chat.type not in ('group','supergroup'):
        return

    # ضد لینک
    if locks['links'].get(m.chat.id) and m.content_type == 'text':
        if re.search(r'(https?://|t\.me|telegram\.me|telegram\.org)', (m.text or '').lower()) and m.from_user.id != SUDO_ID:
            try: bot.delete_message(m.chat.id, m.message_id)
            except: pass

    # ضد استیکر
    if locks['stickers'].get(m.chat.id) and m.content_type == 'sticker':
        try: bot.delete_message(m.chat.id, m.message_id)
        except: pass

    # ضد تبچی (پاک‌کردن پیام‌های تبلیغاتی ساده)
    if locks['tabchi'].get(m.chat.id) and m.content_type == 'text':
        if re.search(r'(اد فور اد|فالو|join|t\.me/|https?://|تبلیغ)', (m.text or '').lower()) and m.from_user.id != SUDO_ID:
            try: bot.delete_message(m.chat.id, m.message_id)
            except: pass

# ===== لفت بده (فقط سودو)
@bot.message_handler(func=lambda m: m.text=="لفت بده")
def leave_cmd(m):
    if m.from_user.id != SUDO_ID: return
    bot.send_message(m.chat.id, "به دستور سودو خارج می‌شوم 👋")
    try: bot.leave_chat(m.chat.id)
    except: pass

print("🤖 Bot is running...")
bot.infinity_polling(timeout=30, long_polling_timeout=30, skip_pending=True)
