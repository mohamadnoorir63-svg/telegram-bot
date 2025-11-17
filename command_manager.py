# ======================== ⚙️ command_manager.py ========================
import os
import json
import random
import shutil
import zipfile
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

ADMIN_ID = 8588347189

# ======================== 📁 مسیرهای اصلی ========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # مسیر auto_brain
DATA_DIR = os.path.join(BASE_DIR, "data")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")

# ساخت پوشه‌ها در صورت عدم وجود
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# مسیر فایل اصلی و بکاپ
DATA_FILE = os.path.join(DATA_DIR, "custom_commands.json")
BACKUP_FILE = os.path.join(BACKUP_DIR, "custom_commands_backup.json")

# ======================== 🔧 فایل‌ها و پوشه‌های مورد نیاز ========================
required_files = [
    DATA_FILE,
    os.path.join(DATA_DIR, "shadow_memory.json"),
    os.path.join(DATA_DIR, "memory.json"),
    os.path.join(DATA_DIR, "group_data.json"),
    os.path.join(DATA_DIR, "fortunes.json"),
    os.path.join(DATA_DIR, "jokes.json"),
    os.path.join(DATA_DIR, "aliases.json"),
    os.path.join(DATA_DIR, "group_control/aliases.json")
]

required_dirs = [
    os.path.join(DATA_DIR, "fortunes_media"),
    os.path.join(DATA_DIR, "jokes_media"),
    os.path.join(DATA_DIR, "group_control")
]

# ساخت پوشه‌ها
for d in required_dirs:
    os.makedirs(d, exist_ok=True)

# ساخت فایل‌های خالی JSON در صورت عدم وجود
for f in required_files:
    if not os.path.exists(f):
        os.makedirs(os.path.dirname(f), exist_ok=True)
        with open(f, "w", encoding="utf-8") as fp:
            json.dump({}, fp, ensure_ascii=False, indent=2)
        print(f"[DEBUG] فایل ساخته شد: {f}")
    else:
        print(f"[DEBUG] فایل موجود است: {f}")

# ======================== 📦 حافظه دستورات ========================
def load_commands():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_commands(data):
    """ذخیره فایل + بکاپ JSON + بکاپ ZIP کامل"""
    try:
        if os.path.exists(DATA_FILE):
            shutil.copy2(DATA_FILE, BACKUP_FILE)
            print(f"[DEBUG] بکاپ JSON ذخیره شد → {BACKUP_FILE}")
    except Exception as e:
        print(f"[WARN] بکاپ JSON ذخیره نشد: {e}")

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[DEBUG] فایل اصلی ذخیره شد → {DATA_FILE}")

    backup_all_commands()

# ======================== 💾 بکاپ ZIP جامع ========================
def backup_all_commands():
    """بکاپ تمام فایل‌ها و پوشه‌های مورد نیاز"""
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    zip_file = os.path.join(BACKUP_DIR, f"full_backup_{now}.zip")

    with zipfile.ZipFile(zip_file, 'w', compression=zipfile.ZIP_DEFLATED) as zipf:
        # بکاپ فایل‌ها و پوشه‌ها
        for f in required_files + required_dirs:
            if os.path.exists(f):
                if os.path.isdir(f):
                    for root, _, files in os.walk(f):
                        for file in files:
                            full_path = os.path.join(root, file)
                            arcname = os.path.relpath(full_path, BASE_DIR)
                            zipf.write(full_path, arcname)
                else:
                    arcname = os.path.relpath(f, BASE_DIR)
                    zipf.write(f, arcname)

    print(f"✅ بکاپ کامل گرفته شد → {zip_file}")

# ======================== 📥 ذخیره دستور (به همراه مدیا داخل required_dirs) ========================
async def save_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    if not context.args:
        return await update.message.reply_text("❗ استفاده: /save <نام> (روی پیام ریپلای کنید)")

    name = " ".join(context.args).strip().lower()
    reply = update.message.reply_to_message

    if not reply:
        return await update.message.reply_text("📎 باید روی یک پیام ریپلای کنید.")

    commands = load_commands()
    doc = commands.get(name, {
        "name": name,
        "responses": [],
        "created": datetime.now().isoformat(),
        "group_id": chat.id if chat.type in ["group", "supergroup"] else None,
        "owner_id": user.id
    })

    entry = {}
    if reply.text:
        entry = {"type": "text", "data": reply.text}
    else:
        file_id = None
        local_path = None

        # برای مدیا، همه داخل jokes_media یا fortunes_media ذخیره می‌کنیم
        media_dir = os.path.join(DATA_DIR, "fortunes_media")  # می‌تونی براساس نوع دستور تغییر بدی
        os.makedirs(media_dir, exist_ok=True)

        if reply.photo:
            file = await reply.photo[-1].get_file()
            local_path = os.path.join(media_dir, f"{name}_{int(datetime.now().timestamp())}.jpg")
            await file.download_to_drive(local_path)
            entry = {"type": "photo", "data": file.file_id, "local": os.path.relpath(local_path, BASE_DIR)}

        elif reply.video:
            file = await reply.video.get_file()
            local_path = os.path.join(media_dir, f"{name}_{int(datetime.now().timestamp())}.mp4")
            await file.download_to_drive(local_path)
            entry = {"type": "video", "data": file.file_id, "local": os.path.relpath(local_path, BASE_DIR)}

        elif reply.document:
            file = await reply.document.get_file()
            ext = os.path.splitext(reply.document.file_name)[1] or ".dat"
            local_path = os.path.join(media_dir, f"{name}_{int(datetime.now().timestamp())}{ext}")
            await file.download_to_drive(local_path)
            entry = {"type": "document", "data": file.file_id, "local": os.path.relpath(local_path, BASE_DIR)}

        elif reply.voice:
            file = await reply.voice.get_file()
            local_path = os.path.join(media_dir, f"{name}_{int(datetime.now().timestamp())}.ogg")
            await file.download_to_drive(local_path)
            entry = {"type": "voice", "data": file.file_id, "local": os.path.relpath(local_path, BASE_DIR)}

        elif reply.animation:
            file = await reply.animation.get_file()
            local_path = os.path.join(media_dir, f"{name}_{int(datetime.now().timestamp())}.mp4")
            await file.download_to_drive(local_path)
            entry = {"type": "animation", "data": file.file_id, "local": os.path.relpath(local_path, BASE_DIR)}

        elif reply.sticker:
            file = await reply.sticker.get_file()
            local_path = os.path.join(media_dir, f"{name}_{int(datetime.now().timestamp())}.webp")
            await file.download_to_drive(local_path)
            entry = {"type": "sticker", "data": file.file_id, "local": os.path.relpath(local_path, BASE_DIR)}

        else:
            return await update.message.reply_text("⚠️ این نوع پیام پشتیبانی نمی‌شود.")

    doc["responses"].append(entry)
    if len(doc["responses"]) > 100:
        doc["responses"].pop(0)

    commands[name] = doc
    save_commands(commands)

    await update.message.reply_text(
        f"✅ پاسخ برای دستور <b>{name}</b> ذخیره شد. ({len(doc['responses'])}/100)",
        parse_mode="HTML"
    )

# ======================== 📤 اجرای دستور ========================
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
        return await update.message.reply_text("⚠️ برای این دستور هنوز پاسخی ثبت نشده.")

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

        context.user_data["custom_handled"] = True

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در اجرای دستور:\n{e}")

# ======================== ❌ حذف دستور ========================
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
        save_commands(commands)
        await update.message.reply_text(f"🗑 دستور '{name}' حذف شد.")
    else:
        await update.message.reply_text("⚠️ دستور پیدا نشد.")

# ======================== 📜 لیست همه دستورها ========================
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
        group = f" | 🏠 {info.get('group_id')}" if info.get("group_id") else ""
        count = len(info.get("responses", []))
        txt += f"🔹 <b>{name}</b> ({count}) — {owner}{group}\n"

    await update.message.reply_text(txt[:4000], parse_mode="HTML")

# ======================== 🧹 پاکسازی دستورات یک گروه ========================
def cleanup_group_commands(chat_id):
    try:
        commands = load_commands()
        new_data = {}
        removed = 0

        for name, info in commands.items():
            if info.get("group_id") == chat_id and info.get("owner_id") != ADMIN_ID:
                removed += 1
                continue
            new_data[name] = info

        save_commands(new_data)
        print(f"🧹 {removed} دستور از گروه {chat_id} حذف شد.")

    except Exception as e:
        print(f"⚠️ خطا: {e}")
