# command_manager.py

import random
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from pymongo import MongoClient

# ====================== تنظیمات ======================
ADMIN_ID = 8588347189
MONGO_URI = "mongodb+srv://username:password@cluster0.gya1hoa.mongodb.net/mydatabase"  # <--- اینجا رشته MongoDB خودت رو بزار
DB_NAME = "mydatabase"
COLLECTION_NAME = "custom_commands"

# ====================== اتصال MongoDB ======================
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
commands_collection = db[COLLECTION_NAME]

# ====================== ذخیره دستور ======================
async def save_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    if not context.args:
        return await update.message.reply_text(
            "❗ استفاده: /save <نام دستور> روی پیام ریپلای شده"
        )

    name = " ".join(context.args).strip().lower()
    reply = update.message.reply_to_message
    if not reply:
        return await update.message.reply_text("📎 باید روی یک پیام ریپلای کنید.")

    # تشخیص نوع پیام
    entry = {}
    if reply.text or reply.caption:
        entry = {"type": "text", "data": reply.text or reply.caption}
    elif reply.photo:
        entry = {"type": "photo", "file_id": reply.photo[-1].file_id, "caption": reply.caption or ""}
    elif reply.video:
        entry = {"type": "video", "file_id": reply.video.file_id, "caption": reply.caption or ""}
    elif reply.document:
        entry = {"type": "document", "file_id": reply.document.file_id, "caption": reply.caption or ""}
    elif reply.audio:
        entry = {"type": "audio", "file_id": reply.audio.file_id, "caption": reply.caption or ""}
    elif reply.animation:
        entry = {"type": "animation", "file_id": reply.animation.file_id, "caption": reply.caption or ""}
    else:
        return await update.message.reply_text("⚠️ این نوع پیام پشتیبانی نمی‌شود!")

    # بررسی وجود دستور قبلی
    doc = commands_collection.find_one({"name": name})
    if not doc:
        doc = {
            "name": name,
            "responses": [],
            "created": datetime.utcnow(),
            "group_id": chat.id if chat.type in ["group", "supergroup"] else None,
            "owner_id": user.id
        }

    doc["responses"].append(entry)
    if len(doc["responses"]) > 100:
        doc["responses"].pop(0)

    commands_collection.update_one({"name": name}, {"$set": doc}, upsert=True)
    await update.message.reply_text(f"✅ پاسخ برای دستور <b>{name}</b> ذخیره شد.", parse_mode="HTML")


# ====================== اجرای دستور ======================
async def handle_custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    doc = commands_collection.find_one({"name": text})
    if not doc or not doc.get("responses"):
        return

    response = random.choice(doc["responses"])
    r_type = response["type"]

    if r_type == "text":
        await update.message.reply_text(response["data"])
    elif r_type == "photo":
        await update.message.reply_photo(response["file_id"], caption=response.get("caption"))
    elif r_type == "video":
        await update.message.reply_video(response["file_id"], caption=response.get("caption"))
    elif r_type == "document":
        await update.message.reply_document(response["file_id"], caption=response.get("caption"))
    elif r_type == "audio":
        await update.message.reply_audio(response["file_id"], caption=response.get("caption"))
    elif r_type == "animation":
        await update.message.reply_animation(response["file_id"], caption=response.get("caption"))


# ====================== حذف دستور ======================
async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی اجازه این کار را دارد.")

    if not context.args:
        return await update.message.reply_text("❗ استفاده: /del <نام دستور>")

    name = " ".join(context.args).strip().lower()
    result = commands_collection.delete_one({"name": name})
    if result.deleted_count:
        await update.message.reply_text(f"🗑 دستور '{name}' حذف شد.")
    else:
        await update.message.reply_text("⚠️ چنین دستوری وجود ندارد.")


# ====================== لیست دستورات ======================
async def list_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجاز است.")

    commands = list(commands_collection.find({}))
    if not commands:
        return await update.message.reply_text("📭 هنوز هیچ دستوری ثبت نشده.")

    txt = "📜 <b>لیست دستورها:</b>\n\n"
    for cmd in commands:
        owner = "👑 سودو" if cmd.get("owner_id") == ADMIN_ID else f"👤 {cmd.get('owner_id')}"
        count = len(cmd.get("responses", []))
        txt += f"🔹 <b>{cmd['name']}</b> ({count}) — {owner}\n"

    await update.message.reply_text(txt[:4000], parse_mode="HTML")


# ====================== پاکسازی دستورات گروه ======================
def cleanup_group_commands(chat_id: int):
    """حذف دستورهایی که در گروه خاص ساخته شده‌اند."""
    removed = commands_collection.delete_many({"group_id": chat_id})
    print(f"[command_manager] cleaned {removed.deleted_count} commands from group {chat_id}")
