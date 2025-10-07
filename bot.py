# -*- coding: utf-8 -*-
import os, json, telebot
from telebot import types

# ========== تنظیمات اولیه ==========
TOKEN = os.environ.get("BOT_TOKEN") or "توکن_خودت_اینجا"
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

DATA_FILE = "data.json"

# ========== بارگذاری / ذخیره داده‌ها ==========
def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"groups": {}, "sudo": [], "bot_admins": []}, f, ensure_ascii=False, indent=2)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()

# ========== توابع کمکی ==========
def is_sudo(uid):
    return uid in data["sudo"]

def is_bot_admin(uid):
    return uid in data["bot_admins"] or is_sudo(uid)

def is_group_admin(chat_id, uid):
    g = data["groups"].get(str(chat_id), {})
    admins = g.get("admins", [])
    return uid in admins or is_bot_admin(uid)

def ensure_group(chat_id):
    chat_id = str(chat_id)
    if chat_id not in data["groups"]:
        data["groups"][chat_id] = {
            "admins": [],
            "welcome": {"status": False, "text": "", "photo": ""},
            "locks": {},
        }

# ========== دستورات مدیریت سودو ==========
@bot.message_handler(commands=["افزودن_سودو"])
def add_sudo(m):
    if not is_sudo(m.from_user.id): return
    if not m.reply_to_message: return bot.reply_to(m, "👤 باید روی پیام فرد مورد نظر ریپلای کنی.")
    uid = m.reply_to_message.from_user.id
    if uid not in data["sudo"]:
        data["sudo"].append(uid)
        save_data()
        bot.reply_to(m, "✅ سودو جدید با موفقیت اضافه شد.")
    else:
        bot.reply_to(m, "⚠️ این کاربر از قبل سودو بوده.")

@bot.message_handler(commands=["حذف_سودو"])
def del_sudo(m):
    if not is_sudo(m.from_user.id): return
    if not m.reply_to_message: return bot.reply_to(m, "👤 روی پیام فردی که می‌خوای حذف شه ریپلای کن.")
    uid = m.reply_to_message.from_user.id
    if uid in data["sudo"]:
        data["sudo"].remove(uid)
        save_data()
        bot.reply_to(m, "❌ سودو حذف شد.")
    else:
        bot.reply_to(m, "⚠️ این کاربر سودو نیست.")

@bot.message_handler(commands=["لیست_سودو"])
def list_sudo(m):
    if not is_sudo(m.from_user.id): return
    if not data["sudo"]: return bot.reply_to(m, "هیچ سودویی ثبت نشده 😅")
    txt = "\n".join([f"• <code>{i}</code>" for i in data["sudo"]])
    bot.reply_to(m, f"👑 لیست سودوها:\n{txt}")

# ========== مدیریت مدیران ربات ==========
@bot.message_handler(commands=["افزودن_مدیر_ربات"])
def add_bot_admin(m):
    if not is_sudo(m.from_user.id): return
    if not m.reply_to_message: return bot.reply_to(m, "👤 باید روی پیام طرف ریپلای کنی.")
    uid = m.reply_to_message.from_user.id
    if uid not in data["bot_admins"]:
        data["bot_admins"].append(uid)
        save_data()
        bot.reply_to(m, "✅ مدیر ربات با موفقیت اضافه شد.")
    else:
        bot.reply_to(m, "⚠️ این کاربر از قبل مدیر رباته.")

@bot.message_handler(commands=["حذف_مدیر_ربات"])
def del_bot_admin(m):
    if not is_sudo(m.from_user.id): return
    if not m.reply_to_message: return bot.reply_to(m, "👤 روی پیام فردی که می‌خوای حذف شه ریپلای کن.")
    uid = m.reply_to_message.from_user.id
    if uid in data["bot_admins"]:
        data["bot_admins"].remove(uid)
        save_data()
        bot.reply_to(m, "❌ مدیر ربات حذف شد.")
    else:
        bot.reply_to(m, "⚠️ این کاربر مدیر ربات نیست.")

@bot.message_handler(commands=["لیست_مدیران_ربات"])
def list_bot_admins(m):
    if not is_bot_admin(m.from_user.id): return
    if not data["bot_admins"]: return bot.reply_to(m, "هیچ مدیر رباتی ثبت نشده 😅")
    txt = "\n".join([f"• <code>{i}</code>" for i in data["bot_admins"]])
    bot.reply_to(m, f"🧑‍💻 لیست مدیران ربات:\n{txt}")

# ========== مدیریت مدیران گروه ==========
@bot.message_handler(commands=["افزودن_مدیر"])
def add_group_admin(m):
    if not (is_bot_admin(m.from_user.id) or is_sudo(m.from_user.id)): return
    if not m.reply_to_message: return bot.reply_to(m, "👤 باید روی پیام کاربر ریپلای کنی.")
    ensure_group(m.chat.id)
    uid = m.reply_to_message.from_user.id
    admins = data["groups"][str(m.chat.id)]["admins"]
    if uid not in admins:
        admins.append(uid)
        save_data()
        bot.reply_to(m, "✅ مدیر گروه با موفقیت اضافه شد.")
    else:
        bot.reply_to(m, "⚠️ این کاربر از قبل مدیر گروهه.")

@bot.message_handler(commands=["حذف_مدیر"])
def del_group_admin(m):
    if not (is_bot_admin(m.from_user.id) or is_sudo(m.from_user.id)): return
    if not m.reply_to_message: return bot.reply_to(m, "👤 روی پیام فردی که می‌خوای حذفش کنی ریپلای کن.")
    ensure_group(m.chat.id)
    uid = m.reply_to_message.from_user.id
    admins = data["groups"][str(m.chat.id)]["admins"]
    if uid in admins:
        admins.remove(uid)
        save_data()
        bot.reply_to(m, "❌ مدیر از گروه حذف شد.")
    else:
        bot.reply_to(m, "⚠️ این کاربر مدیر گروه نیست.")

@bot.message_handler(commands=["لیست_مدیران"])
def list_group_admins(m):
    ensure_group(m.chat.id)
    admins = data["groups"][str(m.chat.id)]["admins"]
    if not admins:
        return bot.reply_to(m, "📭 هیچ مدیری برای این گروه ثبت نشده.")
    txt = "\n".join([f"• <code>{i}</code>" for i in admins])
    bot.reply_to(m, f"👮 لیست مدیران این گروه:\n{txt}")

# ========== تست اولیه ==========
@bot.message_handler(commands=["start"])
def start(m):
    bot.reply_to(m, "سلام رفیق 😎\nمن ربات مدیریت گروه هستم.\nفعلاً بخش مدیریت فعال شده ✅")

# ========== اجرای ربات ==========
print("🤖 Bot is running...")
bot.infinity_polling(skip_pending=True)
