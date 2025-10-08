# -*- coding: utf-8 -*-
import os, json, random
from datetime import datetime
import pytz, jdatetime
import telebot

# ================== ⚙️ تنظیمات ==================
TOKEN   = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
sudo_ids = {SUDO_ID}

# ================== 💾 فایل داده ==================
DATA_FILE = "data.json"

# ساخت اولیه فایل داده
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"groups": {}, "welcome": {}, "autolock": {}}, f, ensure_ascii=False, indent=2)

def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {"groups": {}, "welcome": {}, "autolock": {}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- رفع خودکار خطای KeyError 'welcome' ---
def fix_data():
    data = load_data()
    if "welcome" not in data: data["welcome"] = {}
    if "groups" not in data: data["groups"] = {}
    if "autolock" not in data: data["autolock"] = {}
    save_data(data)
    return data

# ================== 🧩 توابع کمکی ==================
def is_sudo(uid): return uid in sudo_ids
def is_admin(chat_id, user_id):
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator", "creator")
    except: return False

def cmd_text(m): return (getattr(m, "text", None) or "").strip()

# ================== 🕓 عمومی ==================
@bot.message_handler(func=lambda m: cmd_text(m) == "ساعت")
def cmd_time(m):
    now_utc = datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S")
    now_teh = datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y-%m-%d %H:%M:%S")
    bot.reply_to(m, f"⏰ UTC: {now_utc}\n⏰ تهران: {now_teh}")

@bot.message_handler(func=lambda m: cmd_text(m) == "آمار")
def cmd_stats(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    try: count = bot.get_chat_member_count(m.chat.id)
    except: count = "نامشخص"
    bot.reply_to(m, f"📊 اعضای گروه: {count}")

@bot.message_handler(func=lambda m: cmd_text(m) == "ایدی")
def cmd_id(m):
    caption = f"🆔 شما: <code>{m.from_user.id}</code>\n🆔 گروه: <code>{m.chat.id}</code>"
    bot.reply_to(m, caption)

SUDO_RESPONSES = ["جونم قربان 😎", "در خدمتم ✌️", "ربات آماده‌ست 🚀", "چه خبر رئیس؟ 🤖"]
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "ربات")
def cmd_sudo(m): bot.reply_to(m, random.choice(SUDO_RESPONSES))

# ================== 🎉 خوشامد ==================
def now_time():
    return jdatetime.datetime.now().strftime("%H:%M  ( %A %d %B %Y )")

@bot.message_handler(content_types=["new_chat_members"])
def welcome_new_member(m):
    try:
        data = fix_data()
        group = str(m.chat.id)
        settings = data["welcome"].get(group, {"enabled": True, "type": "text", "content": None})
        if not settings.get("enabled", True): return
        name = m.new_chat_members[0].first_name or "دوست جدید"
        time_str = now_time()
        text = settings.get("content") or (
            f"سلام {name} عزیز 🌙\n"
            f"به گروه StarryNight خوش اومدی 😎\n\n"
            f"⏰ ساعت الان: {time_str}"
        )
        bot.send_message(m.chat.id, text)
    except Exception as e:
        print(f"⚠️ welcome error: {e}")

@bot.message_handler(func=lambda m: cmd_text(m) in ["خوشامد روشن", "خوشامد خاموش"])
def toggle_welcome(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    data = fix_data()
    group = str(m.chat.id)
    en = (cmd_text(m) == "خوشامد روشن")
    data["welcome"].setdefault(group, {"enabled": True})
    data["welcome"][group]["enabled"] = en
    save_data(data)
    bot.reply_to(m, "✅ خوشامد روشن شد" if en else "🚫 خوشامد خاموش شد")

@bot.message_handler(func=lambda m: cmd_text(m) == "تنظیم خوشامد متن" and m.reply_to_message)
def set_welcome_text(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    data = fix_data()
    group = str(m.chat.id)
    txt = m.reply_to_message.text or ""
    data["welcome"][group] = {"enabled": True, "type": "text", "content": txt}
    save_data(data)
    bot.reply_to(m, "📝 متن خوشامد تنظیم شد. از {name} و {time} می‌تونی استفاده کنی.")

# ================== 🧹 پاکسازی ==================
@bot.message_handler(func=lambda m: (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)) and cmd_text(m)=="پاکسازی")
def clear_all(m):
    deleted=0
    try:
        for i in range(1,201):
            bot.delete_message(m.chat.id,m.message_id-i)
            deleted+=1
    except: pass
    bot.reply_to(m,f"🧹 {deleted} پیام پاک شد")

@bot.message_handler(func=lambda m: (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)) and cmd_text(m).startswith("حذف "))
def delete_n(m):
    try:
        n=int(cmd_text(m).split()[1])
        for i in range(1,n+1):
            bot.delete_message(m.chat.id,m.message_id-i)
        bot.reply_to(m,f"🗑 {n} پیام پاک شد")
    except: bot.reply_to(m,"❗ فرمت درست: حذف 10")

# ================== 🚀 اجرای نهایی ==================
if __name__ == "__main__":
    print("🤖 Bot is running...")
    try:
        bot.infinity_polling(skip_pending=True, timeout=30)
    except Exception as e:
        print(f"❌ Polling error: {e}")
