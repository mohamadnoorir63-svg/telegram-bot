# -*- coding: utf-8 -*-
import os, json, random, jdatetime, pytz
from datetime import datetime
import telebot
from telebot import types as tb

# ================= ⚙️ تنظیمات =================
TOKEN = os.environ.get("BOT_TOKEN") or "توکن_ربات_اینجا"
SUDO_ID = int(os.environ.get("SUDO_ID", "123456789"))

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
sudo_ids = {SUDO_ID}

DATA_FILE = "data.json"
if not os.path.exists(DATA_FILE):
    data = {"admins": [], "sudos": list(sudo_ids), "groups": {}, "welcome": {}, "autolock": {}}
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ================= 🧩 توابع کمکی =================
def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f: return json.load(f)
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)
def is_sudo(uid): return uid in sudo_ids
def is_admin(chat_id, user_id):
    try: return bot.get_chat_member(chat_id, user_id).status in ("administrator", "creator")
    except: return False
def cmd_text(m): return (getattr(m, "text", None) or "").strip()
def register_group(chat_id):
    data = load_data()
    if str(chat_id) not in data["groups"]:
        data["groups"][str(chat_id)] = True
        save_data(data)

# ================= 💬 عمومی =================
@bot.message_handler(func=lambda m: cmd_text(m) == "ساعت")
def cmd_time(m):
    now = jdatetime.datetime.now().strftime("%H:%M  (%A %d %B %Y)")
    bot.reply_to(m, f"🕓 ساعت و تاریخ شمسی:\n{now}")

@bot.message_handler(func=lambda m: cmd_text(m) == "آیدی")
def cmd_id(m):
    caption = f"🆔 شما: <code>{m.from_user.id}</code>\n🆔 چت: <code>{m.chat.id}</code>"
    try:
        photos = bot.get_user_profile_photos(m.from_user.id, limit=1)
        if photos.total_count > 0:
            bot.send_photo(m.chat.id, photos.photos[0][-1].file_id, caption=caption)
        else: bot.reply_to(m, caption)
    except: bot.reply_to(m, caption)

# ================= 😂 جوک و 🔮 فال =================
jokes, fortunes = [], []
def save_item(arr, m):
    if not m.reply_to_message: return
    if m.reply_to_message.text:
        arr.append({"type": "text", "content": m.reply_to_message.text})
    elif m.reply_to_message.photo:
        arr.append({"type": "photo", "file": m.reply_to_message.photo[-1].file_id, "caption": m.reply_to_message.caption or ""})

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "ثبت جوک")
def add_joke(m): save_item(jokes, m); bot.reply_to(m, "😂 جوک ذخیره شد")

@bot.message_handler(func=lambda m: cmd_text(m) == "جوک")
def send_joke(m):
    if not jokes: return bot.reply_to(m, "❗ جوکی ثبت نشده")
    j = random.choice(jokes)
    if j["type"] == "text": bot.send_message(m.chat.id, j["content"])
    else: bot.send_photo(m.chat.id, j["file"], caption=j["caption"])

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "ثبت فال")
def add_fal(m): save_item(fortunes, m); bot.reply_to(m, "🔮 فال ذخیره شد")

@bot.message_handler(func=lambda m: cmd_text(m) == "فال")
def send_fal(m):
    if not fortunes: return bot.reply_to(m, "❗ فالی ثبت نشده")
    f = random.choice(fortunes)
    if f["type"] == "text": bot.send_message(m.chat.id, f["content"])
    else: bot.send_photo(m.chat.id, f["file"], caption=f["caption"])

# ================= 🎉 خوشامد =================
@bot.message_handler(content_types=["new_chat_members"])
def welcome_new(m):
    try:
        register_group(m.chat.id)
        data = load_data()
        group = str(m.chat.id)
        w = data["welcome"].get(group, {"enabled": True, "type": "text"})
        if not w.get("enabled", True): return
        name = m.new_chat_members[0].first_name
        now = jdatetime.datetime.now().strftime("%H:%M ( %A %d %B %Y )")
        text = f"سلام {name} عزیز 🌟\nبه گروه خوش آمدی 😎\nساعت ورود: {now}"
        if w["type"] == "photo" and w.get("file_id"):
            bot.send_photo(m.chat.id, w["file_id"], caption=text)
        else: bot.send_message(m.chat.id, text)
    except Exception as e: print("Welcome error:", e)

@bot.message_handler(func=lambda m: cmd_text(m) in ["خوشامد روشن", "خوشامد خاموش"])
def toggle_welcome(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    data = load_data(); group = str(m.chat.id)
    en = (cmd_text(m) == "خوشامد روشن")
    data["welcome"][group] = data["welcome"].get(group, {"enabled": True})
    data["welcome"][group]["enabled"] = en
    save_data(data)
    bot.reply_to(m, "✅ خوشامد فعال شد" if en else "🚫 خوشامد غیرفعال شد")

@bot.message_handler(func=lambda m: cmd_text(m) == "تنظیم خوشامد متن" and m.reply_to_message)
def set_welcome_text(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    data = load_data(); group = str(m.chat.id)
    data["welcome"][group] = {"enabled": True, "type": "text", "content": m.reply_to_message.text}
    save_data(data)
    bot.reply_to(m, "📝 متن خوشامد تنظیم شد")

@bot.message_handler(func=lambda m: cmd_text(m) == "تنظیم خوشامد عکس" and m.reply_to_message and m.reply_to_message.photo)
def set_welcome_photo(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    data = load_data(); group = str(m.chat.id)
    file_id = m.reply_to_message.photo[-1].file_id
    caption = m.reply_to_message.caption or "👋 خوش آمدی {name}"
    data["welcome"][group] = {"enabled": True, "type": "photo", "file_id": file_id, "content": caption}
    save_data(data)
    bot.reply_to(m, "🖼 خوشامد تصویری تنظیم شد")

# ================= 🔐 قفل‌ها =================
locks = {k:{} for k in ["links","stickers","photo","video","gif","file","music","voice","forward"]}
LOCK_MAP = {
    "لینک": "links", "استیکر": "stickers", "عکس": "photo", "ویدیو": "video",
    "گیف": "gif", "فایل": "file", "موزیک": "music", "ویس": "voice", "فوروارد": "forward"
}
group_lock = {}

@bot.message_handler(func=lambda m: cmd_text(m).startswith("قفل "))
def lock_cmd(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    k = cmd_text(m).replace("قفل ", "", 1)
    if k == "گروه": group_lock[m.chat.id] = True; return bot.reply_to(m, "🔒 گروه بسته شد")
    key = LOCK_MAP.get(k)
    if key: locks[key][m.chat.id] = True; bot.reply_to(m, f"🔒 قفل {k} فعال شد")

@bot.message_handler(func=lambda m: cmd_text(m).startswith("باز کردن "))
def unlock_cmd(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    k = cmd_text(m).replace("باز کردن ", "", 1)
    if k == "گروه": group_lock[m.chat.id] = False; return bot.reply_to(m, "🔓 گروه باز شد")
    key = LOCK_MAP.get(k)
    if key: locks[key][m.chat.id] = False; bot.reply_to(m, f"🔓 قفل {k} باز شد")

# ================= 📎 لینک و پن =================
@bot.message_handler(func=lambda m: cmd_text(m) == "لینک")
def get_link(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    try:
        link = bot.export_chat_invite_link(m.chat.id)
        bot.reply_to(m, f"🔗 لینک گروه:\n{link}")
    except:
        bot.reply_to(m, "❗ نتونستم لینک بگیرم، باید ادمین باشم.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "پن")
def pin_msg(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    try:
        bot.pin_chat_message(m.chat.id, m.reply_to_message.message_id)
        bot.reply_to(m, "📌 پیام پین شد.")
    except: bot.reply_to(m, "❗ خطا در پین پیام")

@bot.message_handler(func=lambda m: cmd_text(m) == "حذف پن")
def unpin_msg(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    try:
        bot.unpin_all_chat_messages(m.chat.id)
        bot.reply_to(m, "🧹 تمام پیام‌های پین حذف شدند.")
    except: bot.reply_to(m, "❗ خطا در حذف پن")

# ================= ✉️ ارسال همگانی =================
waiting = {}
@bot.message_handler(func=lambda m: cmd_text(m) == "ارسال همگانی")
def ask_broadcast(m):
    if not is_sudo(m.from_user.id): return
    waiting[m.from_user.id] = True
    bot.reply_to(m, "📝 لطفاً پیام همگانی را بفرست:")

@bot.message_handler(func=lambda m: m.from_user.id in waiting)
def do_broadcast(m):
    if not is_sudo(m.from_user.id): return
    text = m.text
    waiting.pop(m.from_user.id, None)
    data = load_data()
    groups = data.get("groups", {})
    sent = 0
    for gid in groups.keys():
        try: bot.send_message(int(gid), f"📢 پیام همگانی:\n{text}"); sent += 1
        except: pass
    bot.reply_to(m, f"✅ پیام به {sent} گروه ارسال شد")

# ================= 🧭 پنل مدیریتی =================
@bot.message_handler(func=lambda m: cmd_text(m) == "پنل")
def panel(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    kb = tb.InlineKeyboardMarkup()
    kb.row(tb.InlineKeyboardButton("🎉 خوشامد", callback_data="panel_welcome"),
           tb.InlineKeyboardButton("📎 لینک", callback_data="panel_link"))
    kb.row(tb.InlineKeyboardButton("✉️ همگانی", callback_data="panel_bcast"),
           tb.InlineKeyboardButton("👮 مدیران", callback_data="panel_admins"))
    kb.add(tb.InlineKeyboardButton("📘 راهنما", callback_data="panel_help"))
    bot.send_message(m.chat.id, "🧭 پنل مدیریت:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data == "panel_help")
def cb_help(c):
    text = (
        "📘 <b>راهنمای دستورات:</b>\n"
        "• قفل‌ها: قفل لینک / استیکر / گیف / ویدیو / گروه\n"
        "• مدیریت: بن / سکوت / اخطار / پاکسازی / حذف [عدد]\n"
        "• خوشامد: تنظیم خوشامد متن / عکس / روشن / خاموش\n"
        "• تفریحی: فال / جوک\n"
        "• سودو: ارسال همگانی / مدیر / سودو\n"
    )
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data == "panel_link")
def cb_link(c):
    get_link(c.message)

@bot.callback_query_handler(func=lambda c: c.data == "panel_bcast")
def cb_bcast(c):
    if not is_sudo(c.from_user.id): return bot.answer_callback_query(c.id, "فقط برای سودو", show_alert=True)
    waiting[c.from_user.id] = True
    bot.answer_callback_query(c.id)
    bot.send_message(c.message.chat.id, "📝 پیام همگانی را بفرست:")

@bot.callback_query_handler(func=lambda c: c.data == "panel_welcome")
def cb_welcome(c):
    bot.answer_callback_query(c.id, "برای تنظیم خوشامد از:\nتنظیم خوشامد متن / عکس استفاده کن.", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data == "panel_admins")
def cb_admins(c):
    data = load_data()
    lst = data.get("admins", [])
    txt = "❗ هیچ مدیری ثبت نشده." if not lst else "\n".join([f"▪️ {uid}" for uid in lst])
    bot.answer_callback_query(c.id)
    bot.send_message(c.message.chat.id, "👮 لیست مدیران:\n" + txt)

# ================= پایان مرحله ۱ =================


print("🤖 Bot is running...")
bot.infinity_polling(skip_pending=True, timeout=30)
