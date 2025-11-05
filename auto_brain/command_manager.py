# ======================== ⚙️ command_manager.py ========================
import os, json, random
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

# 📁 مسیر فایل دستورات
DATA_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "custom_commands.json"))
ADMIN_ID = 8588347189

# ======================== 📦 حافظه دستورات ========================

def load_commands():
    """خواندن تمام دستورها از فایل JSON"""
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_commands(data):
    """ذخیره دستورها در فایل JSON"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

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
        return await update.message.reply_text("📎 باید روی پیامی ریپلای کنی تا ذخیره شود.")

    # بارگذاری داده‌های قبلی
    commands = load_commands()
    doc = commands.get(name, {
        "name": name,
        "responses": [],
        "created": datetime.now().isoformat(),
        "group_id": chat.id if chat.type in ["group", "supergroup"] else None,
        "owner_id": user.id
    })

    # استخراج محتوا از پیام ریپلای شده
    entry = {}
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
        return await update.message.reply_text("⚠️ نوع این پیام پشتیبانی نمی‌شود.")

    # اضافه‌کردن پاسخ جدید (حداکثر 100 مورد)
    doc["responses"].append(entry)
    if len(doc["responses"]) > 100:
        doc["responses"].pop(0)

    commands[name] = doc
    save_commands(commands)

    await update.message.reply_text(
        f"✅ پاسخ جدید برای دستور <b>{name}</b> ذخیره شد ({len(doc['responses'])}/100).",
        parse_mode="HTML"
    )

# ======================== 📤 اجرای دستور ========================

async def handle_custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اجرای دستور ذخیره‌شده"""
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

    # 🎲 انتخاب تصادفی از بین پاسخ‌ها
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

        # جلوگیری از پاسخ اضافی ربات (reply اصلی)
        context.user_data["custom_handled"] = True

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در اجرای دستور:\n{e}")

# ======================== ❌ حذف دستور ========================

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف دستور با /del <نام>"""
    user = update.effective_user
    if user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه.")
    if not context.args:
        return await update.message.reply_text("❗ استفاده: /del <نام دستور>")

    name = " ".join(context.args).strip().lower()
    commands = load_commands()

    if name in commands:
        del commands[name]
        save_commands(commands)
        await update.message.reply_text(f"🗑 دستور '{name}' حذف شد.")
    else:
        await update.message.reply_text("⚠️ چنین دستوری وجود ندارد.")

# ======================== 📜 لیست تمام دستورها ========================

async def list_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست تمام دستورهای ذخیره‌شده"""
    user = update.effective_user
    if user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه لیست رو ببینه.")

    commands = load_commands()
    if not commands:
        return await update.message.reply_text("📭 هنوز هیچ دستوری ذخیره نشده.")

    text = "📜 <b>لیست دستورهای ذخیره‌شده:</b>\n\n"
    for name, info in commands.items():
        owner = "👑 سودو" if info.get("owner_id") == ADMIN_ID else f"👤 {info.get('owner_id')}"
        group = info.get("group_id")
        count = len(info.get("responses", []))
        text += f"🔹 <b>{name}</b> ({count}) — {owner}"
        if group:
            text += f" | 🏠 گروه: {group}"
        text += "\n"

    if len(text) > 4000:
        text = text[:3990] + "..."

    await update.message.reply_text(text, parse_mode="HTML")

# ======================== 🧹 پاکسازی دستورات گروه ========================

def cleanup_group_commands(chat_id):
    """حذف دستورهای ساخته‌شده در گروه مشخص"""
    try:
        commands = load_commands()
        new_data = {}
        removed = 0

        for name, info in commands.items():
            group = info.get("group_id")
            owner = info.get("owner_id")

            # فقط دستورهای همان گروه حذف شوند، دستورات ADMIN_ID باقی بمانند
            if group == chat_id and owner != ADMIN_ID:
                removed += 1
                continue
            new_data[name] = info

        save_commands(new_data)
        print(f"🧹 {removed} دستور مربوط به گروه {chat_id} حذف شد.")
    except Exception as e:
        print(f"⚠️ خطا در پاکسازی دستورات گروه {chat_id}: {e}")
