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

    # ======= ساخت ساختار چندبخشی =======
    parts = []

    if reply.text:
        parts.append({"type": "text", "data": reply.text.strip()})
    if reply.caption:
        parts.append({"type": "text", "data": reply.caption.strip()})
    if reply.photo:
        parts.append({"type": "photo", "file_id": reply.photo[-1].file_id})
    if reply.video:
        parts.append({"type": "video", "file_id": reply.video.file_id})
    if reply.document:
        parts.append({"type": "document", "file_id": reply.document.file_id})
    if reply.audio:
        parts.append({"type": "audio", "file_id": reply.audio.file_id})
    if reply.animation:
        parts.append({"type": "animation", "file_id": reply.animation.file_id})

    if not parts:
        return await update.message.reply_text("⚠️ این نوع پیام پشتیبانی نمی‌شود!")

    entry = {
        "type": "multi",
        "parts": parts
    }

    # جلوگیری از ذخیره‌ی تکراری
    if entry not in doc["responses"]:
        doc["responses"].append(entry)
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


# اجرای دستور بدون تکرار تا مصرف تمام پاسخ‌ها
async def handle_custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    chat = update.effective_chat
    text = update.message.text.strip().lower()
    commands = load_commands()

    if text not in commands:
        return  # دستور سفارشی نیست

    cmd = commands[text]

    # ================= 🎯 منطق دسترسی =================
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

    # ================= اجرای پاسخ =================
    responses = cmd.get("responses", [])
    if not responses:
        return await update.message.reply_text("⚠️ هنوز پاسخی برای این دستور ثبت نشده.")

    used = cmd.get("last_used", [])
    if len(used) >= len(responses):
        used = []

    unused = [i for i in range(len(responses)) if i not in used]
    chosen_index = random.choice(unused)
    chosen = responses[chosen_index]

    used.append(chosen_index)
    cmd["last_used"] = used
    commands[text] = cmd
    save_commands_local(commands)

    # ====== ارسال چندبخشی ======
    if chosen["type"] == "multi":
        for p in chosen["parts"]:
            t = p["type"]
            if t == "text":
                await update.message.reply_text(p["data"])
            elif t == "photo":
                await update.message.reply_photo(p["file_id"])
            elif t == "video":
                await update.message.reply_video(p["file_id"])
            elif t == "document":
                await update.message.reply_document(p["file_id"])
            elif t == "audio":
                await update.message.reply_audio(p["file_id"])
            elif t == "animation":
                await update.message.reply_animation(p["file_id"])

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
