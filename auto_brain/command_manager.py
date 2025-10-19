# ======================== 🧠 command_manager.py (لوکال روی هاست) ========================
import json, os, random
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

DATA_FILE = "data/commands.json"
os.makedirs("data", exist_ok=True)

ADMIN_ID = 7089376754  # آیدی عددی مدیر اصلی (تو)

# ======================== 🧩 ابزار ذخیره‌سازی ========================

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ======================== 📥 ذخیره دستور ========================

async def save_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ذخیره دستور جدید با /save <نام> (روی پیام ریپلای کن)"""
    user = update.effective_user
    if not context.args:
        return await update.message.reply_text("❗ فرمت درست: /save <نام دستور> (روی پیام ریپلای کن)")

    name = " ".join(context.args).strip().lower()
    reply = update.message.reply_to_message
    if not reply:
        return await update.message.reply_text("📎 باید روی پیامی ریپلای کنی تا ذخیره شود.")

    data = load_data()
    if name not in data:
        data[name] = {
            "created_by": user.id,
            "type": None,
            "data": [],
            "settings": {"access": ["everyone"], "mode": "all", "creator_only": False},
            "created": datetime.now().isoformat()
        }

    cmd = data[name]
    if reply.text:
        cmd["type"] = "text"
        cmd["data"].append(reply.text)
    elif reply.photo:
        cmd["type"] = "photo"
        cmd["data"].append(reply.photo[-1].file_id)
    elif reply.video:
        cmd["type"] = "video"
        cmd["data"].append(reply.video.file_id)
    elif reply.document:
        cmd["type"] = "document"
        cmd["data"].append(reply.document.file_id)
    elif reply.voice:
        cmd["type"] = "voice"
        cmd["data"].append(reply.voice.file_id)
    elif reply.animation:
        cmd["type"] = "animation"
        cmd["data"].append(reply.animation.file_id)
    elif reply.sticker:
        cmd["type"] = "sticker"
        cmd["data"].append(reply.sticker.file_id)
    else:
        return await update.message.reply_text("⚠️ نوع این پیام پشتیبانی نمی‌شود.")

    save_data(data)
    await update.message.reply_text(f"✅ دستور '{name}' ذخیره شد!")

# ======================== 📤 اجرای دستور ========================

async def handle_custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فراخوانی دستور ذخیره‌شده با نوشتن اسم آن"""
    text = update.message.text.strip().lower()
    data = load_data()
    cmd = data.get(text)
    if not cmd:
        return

    user_id = update.effective_user.id
    chat_type = update.message.chat.type

    # 🔒 بررسی تنظیمات
    s = cmd.get("settings", {})
    if s.get("creator_only") and user_id not in [cmd["created_by"], ADMIN_ID]:
        return  # فقط سازنده یا ادمین اصلی

    if "admins" in s.get("access", []) and chat_type.endswith("group"):
        member = await update.effective_chat.get_member(user_id)
        if not member.status in ["administrator", "creator"]:
            return

    if "private" not in s.get("access", []) and chat_type == "private" and "everyone" not in s["access"]:
        return

    if "groups" not in s.get("access", []) and chat_type != "private" and "everyone" not in s["access"]:
        return

    try:
        mode = s.get("mode", "all")
        if cmd["type"] == "text":
            if mode == "random":
                await update.message.reply_text(random.choice(cmd["data"]))
            else:
                for d in cmd["data"]:
                    await update.message.reply_text(d)
        elif cmd["type"] == "photo":
            files = cmd["data"] if mode == "all" else [random.choice(cmd["data"])]
            for f in files:
                await update.message.reply_photo(f)
        elif cmd["type"] == "video":
            files = cmd["data"] if mode == "all" else [random.choice(cmd["data"])]
            for f in files:
                await update.message.reply_video(f)
        elif cmd["type"] == "document":
            files = cmd["data"] if mode == "all" else [random.choice(cmd["data"])]
            for f in files:
                await update.message.reply_document(f)
        elif cmd["type"] == "voice":
            files = cmd["data"] if mode == "all" else [random.choice(cmd["data"])]
            for f in files:
                await update.message.reply_voice(f)
        elif cmd["type"] == "animation":
            files = cmd["data"] if mode == "all" else [random.choice(cmd["data"])]
            for f in files:
                await update.message.reply_animation(f)
        elif cmd["type"] == "sticker":
            files = cmd["data"] if mode == "all" else [random.choice(cmd["data"])]
            for f in files:
                await update.message.reply_sticker(f)
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در اجرای دستور:\n{e}")

# ======================== 🗑 حذف دستور ========================

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف دستور با /del <نام>"""
    user = update.effective_user
    if not context.args:
        return await update.message.reply_text("❗ فرمت درست: /del <نام دستور>")

    name = " ".join(context.args).strip().lower()
    data = load_data()
    cmd = data.get(name)
    if not cmd:
        return await update.message.reply_text("⚠️ چنین دستوری وجود ندارد.")

    if user.id != cmd["created_by"] and user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط سازنده یا مدیر اصلی می‌تواند حذف کند.")

    del data[name]
    save_data(data)
    await update.message.reply_text(f"🗑 دستور '{name}' حذف شد.")
