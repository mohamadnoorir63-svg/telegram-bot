import json
from telegram import Update
from telegram.ext import ContextTypes

# ==================== ⚙️ تنظیمات اولیه ====================
ADMINS_FILE = "admins.json"
ALIASES_FILE = "aliases.json"
WARN_FILE = "warnings.json"

MAIN_ADMIN = 123456789  # ← آیدی مدیر اصلی خودت
SUDO_IDS = [MAIN_ADMIN]  # لیست سودوها، بعداً قابل افزایش از کد اصلی

# ==================== 🧩 توابع کمکی ====================
def load_json(file, default):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ------------------ فایل‌ها ------------------
ADMINS = load_json(ADMINS_FILE, [])
ALIASES = load_json(ALIASES_FILE, {
    "ban": "ban",
    "unban": "unban",
    "mute": "mute",
    "unmute": "unmute",
    "warn": "warn",
    "warns": "warns",
    "addmanager": "addmanager",
    "delmanager": "delmanager",
    "listmanagers": "listmanagers"
})
WARNINGS = load_json(WARN_FILE, {})

# ==================== 🧠 بررسی دسترسی ====================
def is_admin(user_id):
    return user_id == MAIN_ADMIN or user_id in SUDO_IDS or user_id in ADMINS

# ==================== 👑 مدیریت مدیران ====================
async def add_manager(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in SUDO_IDS and user.id != MAIN_ADMIN:
        return await update.message.reply_text("⛔ فقط مدیر اصلی یا سودوها می‌تونن مدیر اضافه کنن.")

    if not context.args:
        return await update.message.reply_text("🔹 استفاده: addmanager <ID>")

    new_id = int(context.args[0])
    if new_id in ADMINS:
        return await update.message.reply_text("⚠️ این کاربر از قبل مدیر هست.")
    ADMINS.append(new_id)
    save_json(ADMINS_FILE, ADMINS)
    await update.message.reply_text(f"✅ کاربر {new_id} به لیست مدیران اضافه شد.")

async def del_manager(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        return await update.message.reply_text("⛔ فقط مدیران مجازند.")

    if not context.args:
        return await update.message.reply_text("🔹 استفاده: delmanager <ID>")

    rem_id = int(context.args[0])
    if rem_id not in ADMINS:
        return await update.message.reply_text("⚠️ این کاربر مدیر نیست.")
    ADMINS.remove(rem_id)
    save_json(ADMINS_FILE, ADMINS)
    await update.message.reply_text(f"🗑️ کاربر {rem_id} از لیست مدیران حذف شد.")

async def list_managers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("⛔ فقط مدیران مجازند.")
    if not ADMINS:
        return await update.message.reply_text("📭 هیچ مدیری ثبت نشده.")
    text = "👑 <b>لیست مدیران:</b>\n\n" + "\n".join([f"- <code>{i}</code>" for i in ADMINS])
    await update.message.reply_text(text, parse_mode="HTML")

# ==================== 🔨 بن، سکوت و اخطار ====================
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("⛔ فقط مدیران می‌تونن بن کنن.")
    if not update.message.reply_to_message:
        return await update.message.reply_text("🔹 روی پیام کاربر ریپلای کن تا بن بشه.")
    user = update.message.reply_to_message.from_user
    await context.bot.ban_chat_member(update.effective_chat.id, user.id)
    await update.message.reply_text(f"🚫 {user.first_name} بن شد.")

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("⛔ فقط مدیران می‌تونن آزاد کنن.")
    if not context.args:
        return await update.message.reply_text("🔹 استفاده: unban <ID>")
    user_id = int(context.args[0])
    await context.bot.unban_chat_member(update.effective_chat.id, user_id)
    await update.message.reply_text(f"✅ کاربر {user_id} آزاد شد.")

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("⛔ فقط مدیران می‌تونن سکوت کنن.")
    if not update.message.reply_to_message:
        return await update.message.reply_text("🔹 روی پیام کاربر ریپلای کن تا ساکت بشه.")
    user = update.message.reply_to_message.from_user
    await context.bot.restrict_chat_member(update.effective_chat.id, user.id, permissions={})
    await update.message.reply_text(f"🤫 {user.first_name} ساکت شد.")

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("⛔ فقط مدیران می‌تونن لغو سکوت کنن.")
    if not update.message.reply_to_message:
        return await update.message.reply_text("🔹 روی پیام کاربر ریپلای کن تا آزاد بشه.")
    user = update.message.reply_to_message.from_user
    await context.bot.restrict_chat_member(update.effective_chat.id, user.id, permissions=None)
    await update.message.reply_text(f"✅ {user.first_name} از سکوت خارج شد.")

async def warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("⛔ فقط مدیران می‌تونن اخطار بدن.")
    if not update.message.reply_to_message:
        return await update.message.reply_text("🔹 روی پیام کاربر ریپلای کن تا اخطار بگیره.")

    user = update.message.reply_to_message.from_user
    uid = str(user.id)
    WARNINGS[uid] = WARNINGS.get(uid, 0) + 1

    if WARNINGS[uid] >= 3:
        await context.bot.ban_chat_member(update.effective_chat.id, user.id)
        WARNINGS[uid] = 0
        save_json(WARN_FILE, WARNINGS)
        return await update.message.reply_text(f"🚫 {user.first_name} سه اخطار گرفت و بن شد!")

    save_json(WARN_FILE, WARNINGS)
    await update.message.reply_text(f"⚠️ اخطار {WARNINGS[uid]}/3 برای {user.first_name}")

async def show_warns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("⛔ فقط مدیران مجازند.")
    text = "<b>📋 لیست اخطارها:</b>\n\n"
    if not WARNINGS:
        text += "هیچ اخطاری ثبت نشده."
    else:
        for uid, count in WARNINGS.items():
            text += f"👤 <code>{uid}</code>: {count}/3\n"
    await update.message.reply_text(text, parse_mode="HTML")

# ==================== 🪄 سیستم alias ====================
def get_alias(cmd):
    for key, value in ALIASES.items():
        if cmd.lower() == value.lower():
            return key
    return None
