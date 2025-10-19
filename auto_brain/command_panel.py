# ======================== 🧠 command_manager.py (local version) ========================
import os, json
from datetime import datetime
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest

DATA_FILE = "custom_commands.json"
ADMIN_ID = 7089376754

# ======================== 📦 حافظه دستورات ========================

def load_commands():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_commands(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ======================== 🎛 ساخت پنل ========================

def build_panel_keyboard(name, settings=None):
    if settings is None:
        settings = {"access": ["everyone"], "mode": "all"}

    access = settings.get("access", [])
    mode = settings.get("mode", "all")

    def check(option):
        return "✅" if option in access else "☑️"

    def mode_check(opt):
        return "✅" if opt == mode else "☑️"

    keyboard = [
        [
            InlineKeyboardButton(f"{check('everyone')} همه", callback_data=f"toggle:{name}:everyone"),
            InlineKeyboardButton(f"{check('admins')} ادمین", callback_data=f"toggle:{name}:admins"),
        ],
        [
            InlineKeyboardButton(f"{check('groups')} گروه", callback_data=f"toggle:{name}:groups"),
            InlineKeyboardButton(f"{check('private')} شخصی", callback_data=f"toggle:{name}:private"),
        ],
        [
            InlineKeyboardButton(f"{mode_check('all')} ارسال ثابت", callback_data=f"mode:{name}:all"),
            InlineKeyboardButton(f"{mode_check('random')} تصادفی", callback_data=f"mode:{name}:random"),
        ],
        [
            InlineKeyboardButton("💾 ذخیره", callback_data=f"save:{name}"),
            InlineKeyboardButton("🗑 حذف", callback_data=f"del:{name}"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# ======================== 📥 ذخیره دستور ========================

async def save_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ذخیره دستور جدید با /save <نام>"""
    user = update.effective_user
    if user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه دستور بسازه.")

    if not context.args:
        return await update.message.reply_text("❗ فرمت درست: /save <نام دستور> (روی پیام ریپلای کن)")

    name = " ".join(context.args).strip().lower()
    reply = update.message.reply_to_message

    if not reply:
        return await update.message.reply_text("📎 باید روی پیامی ریپلای کنی تا ذخیره شود.")

    commands = load_commands()

    doc = {
        "name": name,
        "type": None,
        "data": None,
        "created": datetime.now().isoformat(),
        "settings": {"access": ["everyone"], "mode": "all"}
    }

    if reply.text:
        doc["type"] = "text"
        doc["data"] = reply.text
    elif reply.photo:
        doc["type"] = "photo"
        doc["data"] = reply.photo[-1].file_id
    elif reply.video:
        doc["type"] = "video"
        doc["data"] = reply.video.file_id
    elif reply.document:
        doc["type"] = "document"
        doc["data"] = reply.document.file_id
    elif reply.voice:
        doc["type"] = "voice"
        doc["data"] = reply.voice.file_id
    elif reply.animation:
        doc["type"] = "animation"
        doc["data"] = reply.animation.file_id
    elif reply.sticker:
        doc["type"] = "sticker"
        doc["data"] = reply.sticker.file_id
    else:
        return await update.message.reply_text("⚠️ نوع این پیام پشتیبانی نمی‌شود.")

    # ذخیره در فایل JSON
    commands[name] = doc
    save_commands(commands)

    # نمایش پنل تنظیمات
    await update.message.reply_text(
        f"✅ دستور <b>{name}</b> ذخیره شد.\nاکنون تنظیماتش را انتخاب کن 👇",
        parse_mode="HTML",
        reply_markup=build_panel_keyboard(name)
    )

# ======================== 📤 اجرا ========================

async def handle_custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اجرای دستور ذخیره‌شده"""
    text = update.message.text.strip().lower()
    commands = load_commands()
    if text not in commands:
        return

    cmd = commands[text]
    try:
        if cmd["type"] == "text":
            await update.message.reply_text(cmd["data"])
        elif cmd["type"] == "photo":
            await update.message.reply_photo(cmd["data"])
        elif cmd["type"] == "video":
            await update.message.reply_video(cmd["data"])
        elif cmd["type"] == "document":
            await update.message.reply_document(cmd["data"])
        elif cmd["type"] == "voice":
            await update.message.reply_voice(cmd["data"])
        elif cmd["type"] == "animation":
            await update.message.reply_animation(cmd["data"])
        elif cmd["type"] == "sticker":
            await update.message.reply_sticker(cmd["data"])
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در اجرای دستور:\n{e}")

# ======================== ❌ حذف ========================

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف دستور با /del <نام>"""
    user = update.effective_user
    if user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه.")
    if not context.args:
        return await update.message.reply_text("❗ فرمت درست: /del <نام دستور>")

    name = " ".join(context.args).strip().lower()
    commands = load_commands()
    if name in commands:
        del commands[name]
        save_commands(commands)
        await update.message.reply_text(f"🗑 دستور '{name}' حذف شد.")
    else:
        await update.message.reply_text("⚠️ دستوری با این نام یافت نشد.")

# ======================== 🔄 پنل ========================

async def panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت دکمه‌های پنل"""
    query = update.callback_query
    await query.answer()
    data = query.data.split(":")

    if len(data) < 2:
        return

    action, name = data[0], data[1]
    commands = load_commands()
    cmd = commands.get(name)
    if not cmd:
        return await query.edit_message_text("⚠️ دستور حذف شده یا وجود ندارد.")

    settings = cmd.get("settings", {"access": ["everyone"], "mode": "all"})

    if action == "toggle":
        target = data[2]
        if target in settings["access"]:
            settings["access"].remove(target)
        else:
            settings["access"].append(target)

    elif action == "mode":
        settings["mode"] = data[2]

    elif action == "save":
        commands[name]["settings"] = settings
        save_commands(commands)
        return await query.edit_message_text(f"✅ تنظیمات برای '{name}' ذخیره شد!")

    elif action == "del":
        del commands[name]
        save_commands(commands)
        return await query.edit_message_text(f"🗑 دستور '{name}' حذف شد!")

    # آپدیت پنل بدون خطا
    try:
        await query.edit_message_reply_markup(reply_markup=build_panel_keyboard(name, settings))
        commands[name]["settings"] = settings
        save_commands(commands)
    except BadRequest as e:
        if "message is not modified" not in str(e).lower():
            raise e
