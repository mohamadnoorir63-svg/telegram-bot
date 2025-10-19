# ======================== ⚙️ command_manager.py ========================
import os, json
from datetime import datetime
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes

COMMAND_FILE = "commands.json"
ADMIN_ID = 7089376754

# ======================== 💾 مدیریت فایل ========================

def load_commands():
    if not os.path.exists(COMMAND_FILE):
        with open(COMMAND_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
    with open(COMMAND_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_commands(data):
    with open(COMMAND_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ======================== 📥 ذخیره دستور ========================

async def save_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ذخیره دستور با /save <نام> و باز کردن پنل تنظیمات"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه دستور بسازه.")

    if not context.args:
        return await update.message.reply_text("❗ فرمت درست: /save <نام دستور> (روی پیام ریپلای کن)")

    name = " ".join(context.args).strip().lower()
    reply = update.message.reply_to_message
    if not reply:
        return await update.message.reply_text("📎 باید روی پیامی ریپلای کنی تا ذخیره بشه.")

    data = load_commands()

    cmd = {
        "type": None,
        "data": None,
        "settings": {"access": ["everyone"], "mode": "all"},
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # تشخیص نوع پیام
    if reply.text:
        cmd["type"] = "text"
        cmd["data"] = reply.text
    elif reply.photo:
        cmd["type"] = "photo"
        cmd["data"] = reply.photo[-1].file_id
    elif reply.video:
        cmd["type"] = "video"
        cmd["data"] = reply.video.file_id
    elif reply.document:
        cmd["type"] = "document"
        cmd["data"] = reply.document.file_id
    elif reply.voice:
        cmd["type"] = "voice"
        cmd["data"] = reply.voice.file_id
    elif reply.animation:
        cmd["type"] = "animation"
        cmd["data"] = reply.animation.file_id
    elif reply.sticker:
        cmd["type"] = "sticker"
        cmd["data"] = reply.sticker.file_id
    else:
        return await update.message.reply_text("⚠️ این نوع پیام پشتیبانی نمی‌شه.")

    data[name] = cmd
    save_commands(data)

    await update.message.reply_text(f"✅ دستور <b>{name}</b> ذخیره شد!", parse_mode="HTML")

    # ✨ بلافاصله پنل انتخاب تنظیمات رو باز کن
    await show_command_panel(update, context, name)

# ======================== ⚙️ پنل تنظیمات دستور ========================

async def show_command_panel(update: Update, context: ContextTypes.DEFAULT_TYPE, name: str):
    """باز کردن پنل انتخاب تنظیمات برای هر دستور"""
    data = load_commands()
    cmd = data.get(name)
    if not cmd:
        return await update.message.reply_text("⚠️ دستور یافت نشد.")

    settings = cmd.get("settings", {"access": ["everyone"], "mode": "all"})
    await update.message.reply_text(
        f"⚙️ تنظیمات دستور <b>{name}</b>\n"
        "انتخاب کن چه کسانی بتونن ازش استفاده کنن و حالت پاسخ‌دهی چطور باشه:",
        reply_markup=_command_keyboard(name, settings),
        parse_mode="HTML"
    )

def _command_keyboard(name, settings):
    access = settings.get("access", [])
    mode = settings.get("mode", "all")

    def chk(opt): return "✅" if opt in access else "☑️"
    def modechk(opt): return "✅" if opt == mode else "☑️"

    keyboard = [
        [
            InlineKeyboardButton(f"{chk('everyone')} همه", callback_data=f"cmdpanel:{name}:everyone"),
            InlineKeyboardButton(f"{chk('admins')} ادمین", callback_data=f"cmdpanel:{name}:admins"),
        ],
        [
            InlineKeyboardButton(f"{chk('groups')} گروه", callback_data=f"cmdpanel:{name}:groups"),
            InlineKeyboardButton(f"{chk('private')} شخصی", callback_data=f"cmdpanel:{name}:private"),
        ],
        [
            InlineKeyboardButton(f"{modechk('all')} ارسال برای همه", callback_data=f"cmdpanel:{name}:all"),
            InlineKeyboardButton(f"{modechk('random')} تصادفی", callback_data=f"cmdpanel:{name}:random"),
        ],
        [
            InlineKeyboardButton("💾 ذخیره", callback_data=f"cmdpanel:{name}:save"),
            InlineKeyboardButton("🗑 حذف", callback_data=f"cmdpanel:{name}:del"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

# ======================== 🔄 مدیریت کلیک‌ها ========================

async def panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split(":")

    if len(data) < 3:
        return

    action, name, target = data[0], data[1], data[2]
    cmds = load_commands()
    cmd = cmds.get(name)
    if not cmd:
        return await query.edit_message_text("⚠️ دستور یافت نشد.")

    settings = cmd.get("settings", {"access": ["everyone"], "mode": "all"})

    if target in ["everyone", "admins", "groups", "private"]:
        if target in settings["access"]:
            settings["access"].remove(target)
        else:
            settings["access"].append(target)
    elif target in ["all", "random"]:
        settings["mode"] = target
    elif target == "save":
        cmds[name]["settings"] = settings
        save_commands(cmds)
        return await query.edit_message_text(f"✅ تنظیمات '{name}' ذخیره شد.")
    elif target == "del":
        del cmds[name]
        save_commands(cmds)
        return await query.edit_message_text(f"🗑 دستور '{name}' حذف شد.")

    cmds[name]["settings"] = settings
    save_commands(cmds)
    await query.edit_message_reply_markup(reply_markup=_command_keyboard(name, settings))

# ======================== 📤 اجرای دستور ========================

async def handle_custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """وقتی کاربر چیزی نوشت، بررسی کن آیا جزو دستورات ذخیره‌شده هست یا نه"""
    text = update.message.text.strip().lower()
    cmds = load_commands()
    if text not in cmds:
        return

    cmd = cmds[text]
    mode = cmd["settings"].get("mode", "all")

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

# ======================== 🗑 حذف دستور ========================

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه.")

    if not context.args:
        return await update.message.reply_text("❗ فرمت درست: /del <نام دستور>")

    name = " ".join(context.args).strip().lower()
    cmds = load_commands()
    if name in cmds:
        del cmds[name]
        save_commands(cmds)
        await update.message.reply_text(f"🗑 دستور '{name}' حذف شد.")
    else:
        await update.message.reply_text(f"⚠️ دستوری با نام '{name}' پیدا نشد.")
