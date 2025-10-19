# ======================== 🧠 command_manager.py ========================
import json
import os
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

COMMANDS_FILE = "auto_brain/commands_data.json"
ADMIN_ID = 7089376754  # آیدی عددی مدیر اصلی

# ------------------ 📂 توابع ذخیره و بارگذاری ------------------

def load_commands():
    """خواندن دستورات از فایل JSON"""
    if os.path.exists(COMMANDS_FILE):
        with open(COMMANDS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_commands(data):
    """ذخیره دستورات در فایل JSON"""
    with open(COMMANDS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

commands = load_commands()

# ------------------ 💾 ذخیره دستور ------------------

async def save_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ذخیره دستور جدید — /save <نام> (روی پیام ریپلای کن)"""
    user_id = update.effective_user.id
    chat_id = str(update.effective_chat.id)

    if not context.args:
        return await update.message.reply_text("❗ فرمت درست: /save <نام دستور> (روی پیام ریپلای کن)")

    name = " ".join(context.args).strip().lower()
    reply = update.message.reply_to_message

    if not reply:
        return await update.message.reply_text("📎 باید روی پیامی ریپلای کنی تا ذخیره شود.")

    # تشخیص نوع محتوا
    doc = {
        "name": name,
        "type": None,
        "data": None,
        "creator": user_id,
        "chat_id": chat_id,
        "is_global": (user_id == ADMIN_ID),
        "created": datetime.now().isoformat(),
    }

    if reply.text:
        doc["type"] = "text"
        doc["data"] = reply.text
    elif reply.photo:
        doc["type"] = "photo"
        doc["data"] = reply.photo[-1].file_id
    elif reply.video:
        doc["type"] = "video"
        doc["data"] = reply.video.file_id
    elif reply.document:
        doc["type"] = "document"
        doc["data"] = reply.document.file_id
    elif reply.voice:
        doc["type"] = "voice"
        doc["data"] = reply.voice.file_id
    elif reply.animation:
        doc["type"] = "animation"
        doc["data"] = reply.animation.file_id
    elif reply.sticker:
        doc["type"] = "sticker"
        doc["data"] = reply.sticker.file_id
    else:
        return await update.message.reply_text("⚠️ نوع این پیام پشتیبانی نمی‌شود.")

    # ذخیره در لیست
    commands[name] = doc
    save_commands(commands)

    scope = "📢 عمومی" if doc["is_global"] else "👥 فقط برای این گروه"
    await update.message.reply_text(f"✅ دستور '{name}' ذخیره شد! ({scope})")

# ------------------ ⚙️ اجرای دستور ------------------

async def handle_custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فراخوانی دستور ذخیره‌شده با نوشتن نام آن"""
    text = update.message.text.strip().lower()
    chat_id = str(update.effective_chat.id)

    cmd = commands.get(text)
    if not cmd:
        return

    # بررسی سطح دسترسی
    if not cmd["is_global"] and cmd["chat_id"] != chat_id:
        return  # دستور برای این گروه نیست

    try:
        t = cmd["type"]
        if t == "text":
            await update.message.reply_text(cmd["data"])
        elif t == "photo":
            await update.message.reply_photo(cmd["data"])
        elif t == "video":
            await update.message.reply_video(cmd["data"])
        elif t == "document":
            await update.message.reply_document(cmd["data"])
        elif t == "voice":
            await update.message.reply_voice(cmd["data"])
        elif t == "animation":
            await update.message.reply_animation(cmd["data"])
        elif t == "sticker":
            await update.message.reply_sticker(cmd["data"])
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در اجرای دستور:\n{e}")

# ------------------ 🗑 حذف دستور ------------------

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف دستور با /del <نام>"""
    user_id = update.effective_user.id

    if not context.args:
        return await update.message.reply_text("❗ فرمت درست: /del <نام دستور>")

    name = " ".join(context.args).strip().lower()
    cmd = commands.get(name)

    if not cmd:
        return await update.message.reply_text(f"⚠️ دستوری با نام '{name}' یافت نشد.")

    # فقط سازنده یا ادمین اصلی می‌تواند حذف کند
    if user_id != ADMIN_ID and user_id != cmd["creator"]:
        return await update.message.reply_text("⛔ فقط سازنده یا مدیر اصلی می‌تواند حذف کند.")

    del commands[name]
    save_commands(commands)
    await update.message.reply_text(f"🗑 دستور '{name}' حذف شد.")

# ------------------ 🚪 پاکسازی هنگام خروج ربات از گروه ------------------

async def clear_group_commands(chat_id: int):
    """وقتی ربات از گروه خارج شد، دستورات مخصوص اون گروه حذف می‌شن"""
    global commands
    chat_id = str(chat_id)
    before = len(commands)
    commands = {k: v for k, v in commands.items() if v.get("is_global") or v.get("chat_id") != chat_id}
    if len(commands) != before:
        save_commands(commands)
        print(f"🧹 پاکسازی دستورات گروه {chat_id} انجام شد.")
