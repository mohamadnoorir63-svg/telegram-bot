# ======================== ⚙️ command_manager.py ========================
import os, json, random
from datetime import datetime
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest

# 📁 مسیر فایل دستورات
DATA_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "custom_commands.json"))
ADMIN_ID = 7089376754

# ======================== 📦 حافظه دستورات ========================

def load_commands():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_commands(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ======================== 📥 ذخیره دستور ========================

async def save_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ذخیره دستور جدید با /save <نام> (روی پیام ریپلای کن)"""
    user = update.effective_user
    if user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه دستور بسازه.")

    if not context.args:
        return await update.message.reply_text("❗ استفاده: /save <نام دستور> (روی پیام ریپلای کن)")

    name = " ".join(context.args).strip().lower()
    reply = update.message.reply_to_message
    if not reply:
        return await update.message.reply_text("📎 باید روی پیامی ریپلای کنی تا ذخیره شود.")

    commands = load_commands()
    doc = commands.get(name, {
        "name": name,
        "responses": [],
        "created": datetime.now().isoformat(),
    })

    # استخراج داده
    entry = {}
    if reply.text:
        entry = {"type": "text", "data": reply.text}
    elif reply.photo:
        entry = {"type": "photo", "data": reply.photo[-1].file_id}
    elif reply.video:
        entry = {"type": "video", "data": reply.video.file_id}
    elif reply.document:
        entry = {"type": "document", "data": reply.document.file_id}
    elif reply.voice:
        entry = {"type": "voice", "data": reply.voice.file_id}
    elif reply.animation:
        entry = {"type": "animation", "data": reply.animation.file_id}
    elif reply.sticker:
        entry = {"type": "sticker", "data": reply.sticker.file_id}
    else:
        return await update.message.reply_text("⚠️ نوع این پیام پشتیبانی نمی‌شود.")

    # 🧠 اضافه‌کردن پاسخ جدید (حداکثر 100 تا)
    doc["responses"].append(entry)
    if len(doc["responses"]) > 100:
        doc["responses"].pop(0)

    commands[name] = doc
    save_commands(commands)

    await update.message.reply_text(
        f"✅ پاسخ جدید برای دستور <b>{name}</b> ذخیره شد ({len(doc['responses'])}/100).",
        parse_mode="HTML"
    )

# ======================== 📤 اجرای دستور ========================

async def handle_custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اجرای دستور ذخیره‌شده"""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip().lower()
    commands = load_commands()

    if text not in commands:
        return

    cmd = commands[text]
    responses = cmd.get("responses", [])

    if not responses:
        return await update.message.reply_text("⚠️ هنوز پاسخی برای این دستور ثبت نشده.")

    # 🎲 انتخاب تصادفی یکی از پاسخ‌ها
    response = random.choice(responses)
    t, d = response["type"], response["data"]

    try:
        if t == "text":
            await update.message.reply_text(d)
        elif t == "photo":
            await update.message.reply_photo(d)
        elif t == "video":
            await update.message.reply_video(d)
        elif t == "document":
            await update.message.reply_document(d)
        elif t == "voice":
            await update.message.reply_voice(d)
        elif t == "animation":
            await update.message.reply_animation(d)
        elif t == "sticker":
            await update.message.reply_sticker(d)

        # ✅ جلوگیری از اجرای تابع reply بعد از دستور ذخیره‌شده
        context.user_data["custom_handled"] = True

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در اجرای دستور:\n{e}")

# ======================== ❌ حذف دستور ========================

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف دستور با /del <نام>"""
    user = update.effective_user
    if user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه.")
    if not context.args:
        return await update.message.reply_text("❗ استفاده: /del <نام دستور>")

    name = " ".join(context.args).strip().lower()
    commands = load_commands()
    if name in commands:
        del commands[name]
        save_commands(commands)
        await update.message.reply_text(f"🗑 دستور '{name}' حذف شد.")
    else:
        await update.message.reply_text("⚠️ چنین دستوری وجود ندارد.")
