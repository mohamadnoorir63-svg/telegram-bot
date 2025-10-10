# -*- coding: utf-8 -*-
# Persian Tebchi Maker – One File Edition 👑

import os, json, telebot, subprocess, time, textwrap

ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
TOKEN = os.environ.get("BOT_TOKEN")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

DATA_DIR = "data"
BOTS_DIR = os.path.join(DATA_DIR, "bots")
USERS_FILE = os.path.join(DATA_DIR, "users.json")

os.makedirs(BOTS_DIR, exist_ok=True)
if not os.path.exists(USERS_FILE):
    json.dump({}, open(USERS_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ---------------- داده‌ها ----------------
def load_users():
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(d):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

# ---------------- استارت ----------------
@bot.message_handler(commands=["start"])
def start(m):
    uid = str(m.from_user.id)
    users = load_users()
    if uid not in users:
        users[uid] = {"token": None, "created": False}
        save_users(users)

    msg = (
        f"✨ سلام {m.from_user.first_name}!\n"
        "من یه <b>ربات‌ساز تبچی</b> هستم 🤖\n\n"
        "با من می‌تونی ربات خودت رو بسازی که:\n"
        "• پیام همگانی بده 💬\n"
        "• فوروارد کنه 🔁\n"
        "• متن استارت تنظیم کنه ✏️\n\n"
        "فقط کافیه <b>توکن رباتت</b> رو بفرستی 👇"
    )
    bot.reply_to(m, msg)

# ---------------- ثبت توکن ----------------
@bot.message_handler(func=lambda m: len(m.text or "") > 30 and "bot" in m.text)
def save_token(m):
    uid = str(m.from_user.id)
    token = m.text.strip()
    users = load_users()
    users[uid] = {"token": token, "created": False}
    save_users(users)
    bot.reply_to(m, "✅ توکن ذخیره شد.\nحالا بنویس: <b>ساخت ربات</b>")

# ---------------- ساخت ربات ----------------
@bot.message_handler(func=lambda m: m.text == "ساخت ربات")
def make_bot(m):
    uid = str(m.from_user.id)
    users = load_users()
    if uid not in users or not users[uid].get("token"):
        return bot.reply_to(m, "⚠️ اول توکن رباتت رو بفرست.")

    token = users[uid]["token"]
    file_path = os.path.join(BOTS_DIR, f"bot_{uid}.py")

    # قالب خودکار برای ربات کاربر
    template_code = textwrap.dedent(f"""
    import telebot, time, json, os
    TOKEN = "{token}"
    bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
    DATA_FILE = f"data_user_{{TOKEN[:8]}}.json"

    def load_users():
        if not os.path.exists(DATA_FILE):
            json.dump({{"users": []}}, open(DATA_FILE, "w"))
        return json.load(open(DATA_FILE, "r"))

    def save_users(d):
        json.dump(d, open(DATA_FILE, "w"), ensure_ascii=False, indent=2)

    @bot.message_handler(commands=["start"])
    def start(m):
        d = load_users()
        if m.from_user.id not in d["users"]:
            d["users"].append(m.from_user.id)
            save_users(d)
        bot.reply_to(m, "🤖 سلام! این یه ربات خودکاره که پیام همگانی می‌فرسته 💬")

    @bot.message_handler(func=lambda m: m.text == "آمار")
    def stats(m):
        if m.from_user.id == {uid}:
            d = load_users()
            bot.reply_to(m, f"📊 کاربران ثبت‌شده: {{len(d['users'])}}")
    
    @bot.message_handler(func=lambda m: m.text.startswith("ارسال"))
    def send_all(m):
        if m.from_user.id != {uid}: return
        txt = m.text.replace("ارسال", "").strip()
        if not txt: return bot.reply_to(m, "⚠️ بنویس چی بفرستم.")
        d = load_users()
        for u in d["users"]:
            try:
                bot.send_message(u, txt)
                time.sleep(0.1)
            except: pass
        bot.reply_to(m, "✅ پیام برای همه فرستاده شد!")

    @bot.message_handler(func=lambda m: m.text.startswith("فوروارد"))
    def fwd_all(m):
        if m.from_user.id != {uid} or not m.reply_to_message: return
        d = load_users()
        for u in d["users"]:
            try:
                bot.forward_message(u, m.chat.id, m.reply_to_message.id)
                time.sleep(0.1)
            except: pass
        bot.reply_to(m, "🔁 فوروارد برای همه انجام شد!")

    print(f"🤖 Bot for user {uid} is running...")
    bot.infinity_polling(skip_pending=True)
    """)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(template_code)

    users[uid]["created"] = True
    save_users(users)
    bot.reply_to(m, "🚀 رباتت ساخته شد و فعال شد ✅")
    time.sleep(1)
    subprocess.Popen(["python", file_path])

# ---------------- پنل مدیر کل ----------------
@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.text == "پنل")
def admin_panel(m):
    users = load_users()
    total = len(users)
    bots = sum(1 for u in users.values() if u.get("created"))
    msg = (
        "👑 <b>پنل مدیر کل</b>\n\n"
        f"📊 کاربران: {total}\n🤖 ربات‌های ساخته‌شده: {bots}\n\n"
        "دستورات:\n"
        "• لیست کاربران\n"
        "• حذف ربات [آیدی]"
    )
    bot.reply_to(m, msg)

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.text == "لیست کاربران")
def list_users(m):
    users = load_users()
    if not users:
        return bot.reply_to(m, "❌ هیچ کاربری ثبت نشده.")
    msg = "📋 لیست کاربران:\n\n"
    for uid, info in users.items():
        msg += f"👤 {uid} — {'✅ ساخته' if info['created'] else '❌'}\n"
    bot.reply_to(m, msg)

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.text.startswith("حذف ربات"))
def del_bot(m):
    parts = m.text.split()
    if len(parts) < 3:
        return bot.reply_to(m, "مثال: حذف ربات 123456789")
    uid = parts[2]
    path = os.path.join(BOTS_DIR, f"bot_{uid}.py")
    if os.path.exists(path):
        os.remove(path)
        users = load_users()
        users[uid]["created"] = False
        save_users(users)
        bot.reply_to(m, f"🗑️ ربات کاربر {uid} حذف شد.")
    else:
        bot.reply_to(m, "چنین رباتی وجود ندارد.")

# ---------------- اجرا ----------------
print("🤖 Persian Tebchi Maker v1.0 در حال اجراست...")
bot.infinity_polling(skip_pending=True)
