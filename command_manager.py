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


# ================= شروع ذخیره چندمرحله‌ای =================
async def save_command_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("❗ استفاده: /save <نام دستور>")

    # حذف اسلش اول و ترکیب چندکلمه‌ای
    name = " ".join(context.args).lstrip("/").lower()

    context.user_data["saving_command"] = {
        "name": name,
        "responses": []
    }

    await update.message.reply_text(
        f"✅ ذخیره پاسخ‌ها برای دستور <b>{name}</b> شروع شد.\n"
        "📎 هر پیام یا ریپلای که ارسال کنید به عنوان پاسخ ذخیره می‌شود.\n"
        "⛔ برای پایان دادن از دستور /endsave استفاده کنید.",
        parse_mode="HTML"
    )


# ================= ذخیره پیام‌ها در حالت چندمرحله‌ای =================
async def save_command_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data.get("saving_command")
    if not user_data:
        return

    message = update.message
    if not message:
        return

    entry = {}

    # اگر ریپلای باشد، پیام ریپلای را ذخیره کن
    target = message.reply_to_message or message
    text_part = target.text.strip() if target.text else (target.caption.strip() if target.caption else "")

    if target.photo:
        entry = {"type": "photo", "file_id": target.photo[-1].file_id, "caption": text_part or ""}
    elif target.video:
        entry = {"type": "video", "file_id": target.video.file_id, "caption": text_part or ""}
    elif target.document:
        entry = {"type": "document", "file_id": target.document.file_id, "caption": text_part or ""}
    elif target.audio:
        entry = {"type": "audio", "file_id": target.audio.file_id, "caption": text_part or ""}
    elif target.animation:
        entry = {"type": "animation", "file_id": target.animation.file_id, "caption": text_part or ""}
    elif text_part:
        entry = {"type": "text", "data": text_part}
    else:
        entry = {"type": "text", "data": ""}

    if entry not in user_data["responses"]:
        user_data["responses"].append(entry)
        await message.reply_text(f"✅ پاسخ جدید برای دستور <b>{user_data['name']}</b> ذخیره شد.", parse_mode="HTML")
    else:
        await message.reply_text("⚠️ این پاسخ قبلاً ذخیره شده.")


# ================= پایان ذخیره چندمرحله‌ای =================
async def save_command_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data.get("saving_command")
    if not user_data:
        return await update.message.reply_text("⚠️ شما هیچ دستوری در حال ذخیره ندارید.")

    name = user_data["name"]
    responses = user_data["responses"]

    if not responses:
        return await update.message.reply_text("⚠️ هیچ پاسخی ثبت نشده است.")

    commands = load_commands()
    doc = commands.get(name, {
        "name": name,
        "responses": [],
        "created": datetime.now().isoformat(),
        "group_id": update.effective_chat.id if update.effective_chat and update.effective_chat.type in ["group", "supergroup"] else None,
        "owner_id": update.effective_user.id
    })

    for r in responses:
        if r not in doc["responses"]:
            doc["responses"].append(r)

    while len(doc["responses"]) > 200:
        doc["responses"].pop(0)

    commands[name] = doc
    save_commands_local(commands)

    context.user_data.pop("saving_command", None)
    await update.message.reply_text(f"✅ ذخیره پاسخ‌ها برای دستور <b>{name}</b> پایان یافت.", parse_mode="HTML")


# ================= ویرایش دستور =================
async def edit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تواند ویرایش کند.")
    if len(context.args) < 2:
        return await update.message.reply_text("❗ استفاده: /editcmd <نام قبلی> <نام جدید>")

    old_name = context.args[0].lstrip("/").lower()
    new_name = context.args[1].lstrip("/").lower()

    commands = load_commands()
    if old_name not in commands:
        return await update.message.reply_text("⚠️ چنین دستوری وجود ندارد.")

    commands[new_name] = commands.pop(old_name)
    commands[new_name]["name"] = new_name
    save_commands_local(commands)

    await update.message.reply_text(f"✏️ دستور <b>{old_name}</b> به <b>{new_name}</b> تغییر نام یافت.", parse_mode="HTML")


# ================= اجرای دستور =================
async def handle_custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip().lower().lstrip("/")
    commands = load_commands()
    if text not in commands:
        return

    user = update.effective_user
    chat = update.effective_chat
    cmd = commands[text]

    # دسترسی
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

    responses = cmd.get("responses", [])
    if not responses:
        return await update.message.reply_text("⚠️ پاسخی ثبت نشده!")

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

    rt = chosen["type"]
    if rt == "text":
        await update.message.reply_text(chosen["data"])
    elif rt == "photo":
        await update.message.reply_photo(chosen["file_id"], caption=chosen.get("caption"))
    elif rt == "video":
        await update.message.reply_video(chosen["file_id"], caption=chosen.get("caption"))
    elif rt == "document":
        await update.message.reply_document(chosen["file_id"], caption=chosen.get("caption"))
    elif rt == "audio":
        await update.message.reply_audio(chosen["file_id"], caption=chosen.get("caption"))
    elif rt == "animation":
        await update.message.reply_animation(chosen["file_id"], caption=chosen.get("caption"))

    context.user_data["custom_handled"] = True


# ================= لیست دستورها =================
async def list_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجاز است.")

    commands = load_commands()
    if not commands:
        return await update.message.reply_text("📭 هیچ دستوری ثبت نشده.")

    txt = "📜 <b>لیست دستورها:</b>\n\n"
    for name, info in commands.items():
        owner = "👑 سودو" if info.get("owner_id") == ADMIN_ID else f"👤 {info.get('owner_id')}"
        count = len(info.get("responses", []))
        txt += f"🔹 <b>{name}</b> ({count}) — {owner}\n"

    await update.message.reply_text(txt[:4000], parse_mode="HTML")


# ================= حذف دستور =================
async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجاز است.")

    if not context.args:
        return await update.message.reply_text("❗ استفاده: /delcmd <نام دستور>")

    name = context.args[0].lstrip("/").lower()
    commands = load_commands()
    if name not in commands:
        return await update.message.reply_text("⚠️ چنین دستوری وجود ندارد.")

    del commands[name]
    save_commands_local(commands)
    await update.message.reply_text(f"🗑 دستور <b>{name}</b> حذف شد.", parse_mode="HTML")


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
