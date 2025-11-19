# command_manager.py

import os
import json
import random
from datetime import datetime
from typing import Dict, Any
from telegram import Update
from telegram.ext import ContextTypes

# ====== تنظیمات ======
ADMIN_ID = 8588347189

# مسیر همان پوشه‌ای که bot.py و این فایل کنار هم هستند
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_FILE = os.path.join(DATA_DIR, "custom_commands.json")

os.makedirs(DATA_DIR, exist_ok=True)

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)
    print(f"[command_manager] created new data file: {DATA_FILE}")
else:
    print(f"[command_manager] data file exists: {DATA_FILE}")


# ================= توابع کمکی =================
def _load_json(path: str, default: Any = None):
    if default is None:
        default = {}
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
        return default


def _save_json(path: str, data: Any):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def load_commands() -> Dict[str, Any]:
    return _load_json(DATA_FILE, {})


def save_commands_local(data: Dict[str, Any]):
    _save_json(DATA_FILE, data)


# ================= API اصلی =================

# ذخیره دستور با جلوگیری از تکرار و حداکثر 200 پاسخ
async def save_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    if not context.args:
        return await update.message.reply_text(
            "❗ استفاده: /save <نام دستور> (روی پیام ریپلای کنید)"
        )

    name = " ".join(context.args).strip().lower()
    reply = update.message.reply_to_message
    if not reply:
        return await update.message.reply_text("📎 باید روی یک پیام ریپلای کنید.")

    commands = load_commands()
    doc = commands.get(name, {
        "name": name,
        "responses": [],
        "created": datetime.now().isoformat(),
        "group_id": chat.id if chat and chat.type in ["group", "supergroup"] else None,
        "owner_id": user.id
    })

    entry = {}
    if reply.text or reply.caption:
        entry = {"type": "text", "data": (reply.text or reply.caption).strip()}
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

    # جلوگیری از ذخیره‌ی تکراری
    if entry not in doc["responses"]:
        doc["responses"].append(entry)
        # حداکثر 200 پاسخ نگه داشته شود
        while len(doc["responses"]) > 200:
            doc["responses"].pop(0)

        commands[name] = doc
        save_commands_local(commands)
        await update.message.reply_text(
            f"✅ پاسخ برای دستور <b>{name}</b> ذخیره شد. ({len(doc['responses'])}/200)",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text("⚠️ این پاسخ قبلا ذخیره شده و تکراری نمی‌شود.")



# اجرای دستور با ارسال فقط 1 پاسخ تصادفی
async def handle_custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    # فقط یکی از پاسخ‌ها به صورت تصادفی (بدون تکرار)
    response = random.choice(responses)

    r_type = response.get("type")

    if r_type == "text":
        await update.message.reply_text(response.get("data", ""))
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

    context.user_data["custom_handled"] = True
async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی اجازه این کار را دارد.")

    if not context.args:
        return await update.message.reply_text("❗ استفاده: /del <نام دستور>")

    name = " ".join(context.args).strip().lower()
    commands = load_commands()

    if name in commands:
        del commands[name]
        save_commands_local(commands)
        await update.message.reply_text(f"🗑 دستور '{name}' حذف شد.")
    else:
        await update.message.reply_text("⚠️ چنین دستوری وجود ندارد.")


async def list_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجاز است.")

    commands = load_commands()
    if not commands:
        return await update.message.reply_text("📭 هنوز هیچ دستوری ثبت نشده.")

    txt = "📜 <b>لیست دستورها:</b>\n\n"
    for name, info in commands.items():
        owner = "👑 سودو" if info.get("owner_id") == ADMIN_ID else f"👤 {info.get('owner_id')}"
        count = len(info.get("responses", []))
        txt += f"🔹 <b>{name}</b> ({count}) — {owner}\n"

    await update.message.reply_text(txt[:4000], parse_mode="HTML")


def cleanup_group_commands(chat_id: int):
    """حذف دستورهایی که در گروه خاص ساخته شده‌اند."""
    try:
        commands = load_commands()
        new_data = {}
        removed = 0
        for name, info in commands.items():
            if info.get("group_id") == chat_id and info.get("owner_id") != ADMIN_ID:
                removed += 1
                continue
            new_data[name] = info
        save_commands_local(new_data)
        print(f"[command_manager] cleaned {removed} commands from group {chat_id}")
    except Exception as e:
        print(f"[command_manager] cleanup error: {e}")
