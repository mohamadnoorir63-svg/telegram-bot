# ======================== 🧠 command_manager.py (fixed full version) ========================
import os, json, random
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
        settings = {"access": ["everyone"], "targets": ["group", "private"], "mode": "all"}

    access = settings.get("access", ["everyone"])
    targets = settings.get("targets", ["group", "private"])
    mode = settings.get("mode", "all")

    def chk(lst, opt):
        return "✅" if opt in lst else "☑️"

    def mode_chk(opt):
        return "✅" if opt == mode else "☑️"

    keyboard = [
        [
            InlineKeyboardButton(f"{chk(access,'everyone')} همه", callback_data=f"toggle_access:{name}:everyone"),
            InlineKeyboardButton(f"{chk(access,'admins')} ادمین", callback_data=f"toggle_access:{name}:admins"),
        ],
        [
            InlineKeyboardButton(f"{chk(targets,'group')} گروه", callback_data=f"toggle_target:{name}:group"),
            InlineKeyboardButton(f"{chk(targets,'private')} شخصی", callback_data=f"toggle_target:{name}:private"),
        ],
        [
            InlineKeyboardButton(f"{mode_chk('all')} ارسال ثابت", callback_data=f"set_mode:{name}:all"),
            InlineKeyboardButton(f"{mode_chk('random')} تصادفی", callback_data=f"set_mode:{name}:random"),
        ],
        [
            InlineKeyboardButton("💾 ذخیره", callback_data=f"save:{name}"),
            InlineKeyboardButton("🗑 حذف", callback_data=f"delete:{name}"),
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
        "settings": {"access": ["everyone"], "targets": ["group", "private"], "mode": "all"}
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

    # ذخیره یا بروزرسانی
    commands[name] = doc
    save_commands(commands)

    await update.message.reply_text(
        f"✅ دستور <b>{name}</b> ذخیره شد.\nاکنون تنظیماتش را انتخاب کن 👇",
        parse_mode="HTML",
        reply_markup=build_panel_keyboard(name)
    )

# ======================== 📤 اجرا ========================

async def handle_custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اجرای دستور ذخیره‌شده"""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip().lower()
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id

    commands = load_commands()
    if text not in commands:
        return

    cmd = commands[text]
    settings = cmd.get("settings", {"access": ["everyone"], "targets": ["group", "private"], "mode": "all"})

    # دسترسی بر اساس نوع چت
    if chat_type == "private" and "private" not in settings.get("targets", []):
        return
    if chat_type in ["group", "supergroup"] and "group" not in settings.get("targets", []):
        return

    # بررسی سطح دسترسی
    if "admins" in settings.get("access", []) and user_id != ADMIN_ID:
        return  # فقط ادمین اجازه دارد

    try:
        # حالت ارسال: ثابت یا تصادفی
        if settings.get("mode") == "random":
            await send_command_random(update, cmd)
        else:
            await send_command_fixed(update, cmd)
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در اجرای دستور:\n{e}")

async def send_command_fixed(update, cmd):
    """ارسال ثابت"""
    t, d = cmd["type"], cmd["data"]
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

async def send_command_random(update, cmd):
    """ارسال تصادفی (در آینده اگر چند پاسخ اضافه شد)"""
    await send_command_fixed(update, cmd)

# ======================== ❌ حذف ========================

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    settings = cmd.get("settings", {"access": ["everyone"], "targets": ["group", "private"], "mode": "all"})

    if action == "toggle_access":
        target = data[2]
        if target in settings["access"]:
            settings["access"].remove(target)
        else:
            settings["access"].append(target)

    elif action == "toggle_target":
        target = data[2]
        if target in settings["targets"]:
            settings["targets"].remove(target)
        else:
            settings["targets"].append(target)

    elif action == "set_mode":
        settings["mode"] = data[2]

    elif action == "save":
        commands[name]["settings"] = settings
        save_commands(commands)
        return await query.edit_message_text(f"✅ تنظیمات برای '{name}' ذخیره شد!")

    elif action == "delete":
        del commands[name]
        save_commands(commands)
        return await query.edit_message_text(f"🗑 دستور '{name}' حذف شد!")

    # آپدیت پنل بدون خطا
    try:
        commands[name]["settings"] = settings
        save_commands(commands)
        await query.edit_message_reply_markup(reply_markup=build_panel_keyboard(name, settings))
    except BadRequest as e:
        if "message is not modified" not in str(e).lower():
            raise e
