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

# ذخیره دستور با پشتیبانی از چند بخش در یک پکیج
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
        "packages": [],
        "created": datetime.now().isoformat(),
        "group_id": chat.id if chat and chat.type in ["group", "supergroup"] else None,
        "owner_id": user.id
    })

    package = []  # یک پکیج شامل چند پیام

    # متن
    if reply.text or reply.caption:
        package.append({
            "type": "text",
            "data": (reply.text or reply.caption).strip()
        })

    # عکس
    if reply.photo:
        package.append({
            "type": "photo",
            "file_id": reply.photo[-1].file_id,
            "caption": reply.caption or ""
        })

    # ویدیو
    if reply.video:
        package.append({
            "type": "video",
            "file_id": reply.video.file_id,
            "caption": reply.caption or ""
        })

    # فایل
    if reply.document:
        package.append({
            "type": "document",
            "file_id": reply.document.file_id,
            "caption": reply.caption or ""
        })

    # موزیک
    if reply.audio:
        package.append({
            "type": "audio",
            "file_id": reply.audio.file_id,
            "caption": reply.caption or ""
        })

    # گیف
    if reply.animation:
        package.append({
            "type": "animation",
            "file_id": reply.animation.file_id,
            "caption": reply.caption or ""
        })

    if not package:
        return await update.message.reply_text("⚠️ این نوع پیام پشتیبانی نمی‌شود!")

    # اضافه کردن پکیج
    doc["packages"].append(package)

    # محدودیت 200 پکیج
    if len(doc["packages"]) > 200:
        doc["packages"] = doc["packages"][-200:]

    commands[name] = doc
    save_commands_local(commands)

    await update.message.reply_text(
        f"✅ پکیج جدید برای دستور <b>{name}</b> ذخیره شد. ({len(doc['packages'])}/200)",
        parse_mode="HTML"
    )


# ================= اجرای دستور =================
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

    # ===== کنترل دسترسی =====
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

    packages = cmd.get("packages", [])
    if not packages:
        return await update.message.reply_text("⚠️ هنوز پکیجی ثبت نشده.")

    # ===== انتخاب پکیج رندومی بدون تکرار =====
    used = cmd.get("last_used", [])

    if len(used) >= len(packages):
        used = []

    unused = [i for i in range(len(packages)) if i not in used]
    chosen_index = random.choice(unused)
    chosen_package = packages[chosen_index]

    used.append(chosen_index)
    cmd["last_used"] = used
    commands[text] = cmd
    save_commands_local(commands)

    # ===== ارسال کل پکیج =====
    for part in chosen_package:
        t = part["type"]

        if t == "text":
            await update.message.reply_text(part["data"])

        elif t == "photo":
            await update.message.reply_photo(part["file_id"], caption=part.get("caption"))

        elif t == "video":
            await update.message.reply_video(part["file_id"], caption=part.get("caption"))

        elif t == "document":
            await update.message.reply_document(part["file_id"], caption=part.get("caption"))

        elif t == "audio":
            await update.message.reply_audio(part["file_id"], caption=part.get("caption"))

        elif t == "animation":
            await update.message.reply_animation(part["file_id"], caption=part.get("caption"))

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
        count = len(info.get("packages", []))
        txt += f"🔹 <b>{name}</b> ({count} پکیج) — {owner}\n"

    await update.message.reply_text(txt[:4000], parse_mode="HTML")


# ================= حذف دستور =================
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
