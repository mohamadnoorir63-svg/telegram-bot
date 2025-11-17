# ======================== ⚙️ command_manager.py ========================
import os
import json
import random
import shutil
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

# ======================== 📁 مسیرهای امن و استاندارد ========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")

DATA_FILE = os.path.join(DATA_DIR, "custom_commands.json")
BACKUP_FILE = os.path.join(BACKUP_DIR, "custom_commands_backup.json")

ADMIN_ID = 8588347189

# ساخت پوشه‌ها
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# ساخت فایل اولیه
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)
    print(f"[INIT] custom_commands.json ساخته شد.")


# ======================== 📦 خواندن و ذخیره‌سازی ========================
def load_commands():
    """خواندن تمام دستورها از فایل JSON"""
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] خطا در خواندن custom_commands.json: {e}")
        return {}


def save_commands(data):
    """ذخیره دستورها + بکاپ‌گیری مطمئن"""
    try:
        # بکاپ قبل از نوشتن
        if os.path.exists(DATA_FILE):
            shutil.copy2(DATA_FILE, BACKUP_FILE)
            print(f"[BACKUP] بکاپ ذخیره شد در {BACKUP_FILE}")
    except Exception as e:
        print(f"[BACKUP ERROR] بکاپ شکست خورد: {e}")

    # ذخیره اصلی
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("[SAVE] custom_commands.json ذخیره شد.")
    except Exception as e:
        print(f"[ERROR] ذخیره‌سازی شکست خورد: {e}")


# ======================== 📥 ذخیره دستور ========================
async def save_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ذخیره دستور جدید با /save <نام> (روی پیام ریپلای کن)"""
    user = update.effective_user
    chat = update.effective_chat

    if not context.args:
        return await update.message.reply_text("❗ استفاده: /save <نام دستور> (روی پیام ریپلای کن)")

    name = " ".join(context.args).strip().lower()
    reply = update.message.reply_to_message

    if not reply:
        return await update.message.reply_text("📎 باید روی پیامی ریپلای کنی.")

    commands = load_commands()

    doc = commands.get(name, {
        "name": name,
        "responses": [],
        "created": datetime.now().isoformat(),
        "group_id": chat.id if chat.type in ("group", "supergroup") else None,
        "owner_id": user.id
    })

    entry = {}

    # تشخیص نوع پیام
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
        return await update.message.reply_text("⚠️ این نوع پیام پشتیبانی نمی‌شود.")

    # افزودن
    doc["responses"].append(entry)

    # محدودیت 100 پاسخ
    if len(doc["responses"]) > 100:
        doc["responses"].pop(0)

    commands[name] = doc
    save_commands(commands)

    return await update.message.reply_text(
        f"✅ پاسخ برای دستور <b>{name}</b> ذخیره شد.",
        parse_mode="HTML"
    )


# ======================== 📤 اجرای دستور ========================
async def handle_custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    msg = update.message.text.strip().lower()
    commands = load_commands()

    if msg not in commands:
        return

    cmd = commands[msg]
    responses = cmd.get("responses", [])

    if not responses:
        return await update.message.reply_text("⚠️ هنوز پاسخی برای این دستور ذخیره نشده.")

    resp = random.choice(responses)
    t, d = resp["type"], resp["data"]

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

        context.user_data["custom_handled"] = True

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در ارسال:\n{e}")


# ======================== ❌ حذف دستور ========================
async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه.")

    if not context.args:
        return await update.message.reply_text("❗ استفاده: /del <نام>")

    name = " ".join(context.args).strip().lower()

    commands = load_commands()

    if name not in commands:
        return await update.message.reply_text("⚠️ چنین دستوری وجود ندارد.")

    del commands[name]
    save_commands(commands)

    return await update.message.reply_text(f"🗑 دستور '{name}' حذف شد.")


# ======================== 📜 لیست دستورها ========================
async def list_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه.")

    commands = load_commands()

    if not commands:
        return await update.message.reply_text("📭 هنوز هیچ دستوری ثبت نشده.")

    txt = "📜 <b>لیست دستورات:</b>\n\n"

    for name, info in commands.items():
        owner = "👑 سودو" if info.get("owner_id") == ADMIN_ID else f"👤 {info.get('owner_id')}"
        count = len(info.get("responses", []))
        txt += f"🔹 <b>{name}</b> — {count} پاسخ — {owner}\n"

    if len(txt) > 4000:
        txt = txt[:3990] + "…"

    await update.message.reply_text(txt, parse_mode="HTML")


# ======================== 🧹 پاکسازی گروه ========================
def cleanup_group_commands(chat_id):
    try:
        data = load_commands()
        new_data = {}
        removed = 0

        for name, info in data.items():
            if info.get("group_id") == chat_id and info.get("owner_id") != ADMIN_ID:
                removed += 1
                continue
            new_data[name] = info

        save_commands(new_data)
        print(f"[CLEANUP] {removed} دستور پاک شد از گروه {chat_id}")

    except Exception as e:
        print(f"[ERROR] پاک‌سازی شکست خورد: {e}")
