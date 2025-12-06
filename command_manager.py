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

# ذخیره دستور به صورت پکیج چندپیامی
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

    # تابع کمکی برای ساخت آبجکت پیام
    def create_message_obj(msg):
        if msg.text or msg.caption:
            return {"type": "text", "data": (msg.text or msg.caption).strip()}
        elif msg.photo:
            return {"type": "photo", "file_id": msg.photo[-1].file_id, "caption": msg.caption or ""}
        elif msg.video:
            return {"type": "video", "file_id": msg.video.file_id, "caption": msg.caption or ""}
        elif msg.document:
            return {"type": "document", "file_id": msg.document.file_id, "caption": msg.caption or ""}
        elif msg.audio:
            return {"type": "audio", "file_id": msg.audio.file_id, "caption": msg.caption or ""}
        elif msg.animation:
            return {"type": "animation", "file_id": msg.animation.file_id, "caption": msg.caption or ""}
        return None

    # ایجاد پکیج تک‌پیامی از پیام ریپلای شده
    package = []
    obj = create_message_obj(reply)
    if not obj:
        return await update.message.reply_text("⚠️ این نوع پیام پشتیبانی نمی‌شود!")
    package.append(obj)

    # جلوگیری از تکراری بودن پکیج
    if package not in doc["responses"]:
        doc["responses"].append(package)
        while len(doc["responses"]) > 200:
            doc["responses"].pop(0)

        commands[name] = doc
        save_commands_local(commands)
        await update.message.reply_text(
            f"✅ پکیج پاسخ برای دستور <b>{name}</b> ذخیره شد. ({len(doc['responses'])}/200)",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text("⚠️ این پکیج قبلا ذخیره شده و تکراری نمی‌شود.")


# اجرای دستور با ارسال کل پکیج
async def handle_custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    chat = update.effective_chat
    text = update.message.text.strip().lower()
    commands = load_commands()

    if text not in commands:
        return

    cmd = commands[text]

    # بررسی دسترسی
    is_allowed = False
    if chat and chat.type in ["group", "supergroup"]:
        if user.id == ADMIN_ID:
            is_allowed = True
        else:
            try:
                member = await chat.get_member(user.id)
                if member.status in ["administrator", "creator"]:
                    is_allowed = True
            except:
                pass
        if not is_allowed:
            return
    else:
        is_allowed = True

    # اجرای پاسخ
    responses = cmd.get("responses", [])
    if not responses:
        return await update.message.reply_text("⚠️ هنوز پاسخی برای این دستور ثبت نشده.")

    used = cmd.get("last_used", [])
    if len(used) >= len(responses):
        used = []

    unused = [i for i in range(len(responses)) if i not in used]
    chosen_index = random.choice(unused)
    chosen_package = responses[chosen_index]
    used.append(chosen_index)

    cmd["last_used"] = used
    commands[text] = cmd
    save_commands_local(commands)

    # ارسال کل پکیج
    for chosen in chosen_package:
        r_type = chosen.get("type")
        if r_type == "text":
            await update.message.reply_text(chosen.get("data", ""))
        elif r_type == "photo":
            await update.message.reply_photo(chosen.get("file_id"), caption=chosen.get("caption", ""))
        elif r_type == "video":
            await update.message.reply_video(chosen.get("file_id"), caption=chosen.get("caption", ""))
        elif r_type == "document":
            await update.message.reply_document(chosen.get("file_id"), caption=chosen.get("caption", ""))
        elif r_type == "audio":
            await update.message.reply_audio(chosen.get("file_id"), caption=chosen.get("caption", ""))
        elif r_type == "animation":
            await update.message.reply_animation(chosen.get("file_id"), caption=chosen.get("caption", ""))

    context.user_data["custom_handled"] = True


# ================= لیست دستورها =================
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


# ================= پاکسازی دستورات گروه =================
def cleanup_group_commands(chat_id: int):
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


# ================= حذف یک دستور =================
async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجاز است.")

    if not context.args:
        return await update.message.reply_text("❗ استفاده: /delcmd <نام دستور>")

    name = " ".join(context.args).strip().lower()
    commands = load_commands()

    if name not in commands:
        return await update.message.reply_text("⚠️ چنین دستوری وجود ندارد.")

    del commands[name]
    save_commands_local(commands)

    await update.message.reply_text(f"🗑 دستور <b>{name}</b> حذف شد.", parse_mode="HTML")
