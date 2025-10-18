# ======================== 🧠 command_manager.py ========================
from pymongo import MongoClient
from datetime import datetime
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes

# ⚙️ اتصال به MongoDB فقط برای مدیریت دستورات
MONGO_URI = "mongodb+srv://mohamadnoorir63_db_user:cVm8y2ohBnpN2xcn@cluster0.gya1hoa.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)

db = client["khengool_db"]             # دیتابیس مخصوص بخش دستورات
commands = db["custom_commands"]       # کالکشن فقط برای دستورها

ADMIN_ID = 7089376754  # آیدی عددی مدیر اصلی (تو)

# ======================== 📥 ذخیره دستور ========================

async def save_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ذخیره دستور جدید با /save <نام> (روی پیام ریپلای کن)"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تواند دستور بسازد.")

    if not context.args:
        return await update.message.reply_text("❗ فرمت درست: /save <نام دستور> (روی پیام ریپلای کن)")

    name = " ".join(context.args).strip().lower()
    reply = update.message.reply_to_message

    if not reply:
        return await update.message.reply_text("📎 باید روی پیامی ریپلای کنی تا ذخیره شود.")

    doc = {"name": name, "type": None, "data": None, "created": datetime.now()}
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

    commands.update_one({"name": name}, {"$set": doc}, upsert=True)
    await update.message.reply_text(f"✅ دستور '{name}' با موفقیت ذخیره شد!")

# ======================== 📤 اجرا و حذف ========================

async def handle_custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فراخوانی دستور ذخیره‌شده با نوشتن اسم آن"""
    text = update.message.text.strip().lower()
    cmd = commands.find_one({"name": text})
    if not cmd:
        return

    try:
        if cmd["type"] == "text":
            await update.message.reply_text(cmd["data"])
        elif cmd["type"] == "photo":
            await update.message.reply_photo(cmd["data"])
        elif cmd["type"] == "video":
            await update.message.reply_video(cmd["data"])
        elif cmd["type"] == "document":
            await update.message.reply_document(cmd["data"])
        elif cmd["type"] == "voice":
            await update.message.reply_voice(cmd["data"])
        elif cmd["type"] == "animation":
            await update.message.reply_animation(cmd["data"])
        elif cmd["type"] == "sticker":
            await update.message.reply_sticker(cmd["data"])
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در ارسال دستور:\n{e}")

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف دستور با /del <نام>"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه.")

    if not context.args:
        return await update.message.reply_text("❗ فرمت درست: /del <نام دستور>")

    name = " ".join(context.args).strip().lower()
    result = commands.delete_one({"name": name})
    if result.deleted_count:
        await update.message.reply_text(f"🗑 دستور '{name}' حذف شد.")
    else:
        await update.message.reply_text(f"⚠️ دستوری با نام '{name}' یافت نشد.")
