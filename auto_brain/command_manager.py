# ======================== ⚙️ command_manager.py ========================
import os, json, random
from datetime import datetime
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest

# 📁 مسیر فایل دستورات
DATA_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "custom_commands.json"))
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

    access = settings.get("access", [])
    targets = settings.get("targets", [])
    mode = settings.get("mode", "all")

    def check(option, arr):
        return "✅" if option in arr else "☑️"

    keyboard = [
        [
            InlineKeyboardButton(f"{check('everyone', access)} همه", callback_data=f"access:{name}:everyone"),
            InlineKeyboardButton(f"{check('admins', access)} مدیران", callback_data=f"access:{name}:admins"),
        ],
        [
            InlineKeyboardButton(f"{check('group', targets)} گروه", callback_data=f"target:{name}:group"),
            InlineKeyboardButton(f"{check('private', targets)} شخصی", callback_data=f"target:{name}:private"),
        ],
        [
            InlineKeyboardButton(f"{'✅' if mode == 'all' else '☑️'} ارسال ثابت", callback_data=f"mode:{name}:all"),
            InlineKeyboardButton(f"{'✅' if mode == 'random' else '☑️'} تصادفی", callback_data=f"mode:{name}:random"),
        ],
        [
            InlineKeyboardButton("💾 ذخیره", callback_data=f"save:{name}"),
            InlineKeyboardButton("🗑 حذف", callback_data=f"delete:{name}"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# ======================== 📥 ذخیره دستور ========================

async def save_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    doc = commands.get(name, {
        "name": name,
        "responses": [],
        "created": datetime.now().isoformat(),
        "settings": {"access": ["everyone"], "targets": ["group", "private"], "mode": "all"}
    })

    # استخراج داده
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

    doc["responses"].append(entry)
    commands[name] = doc
    save_commands(commands)

    await update.message.reply_text(
        f"✅ پاسخ جدید برای دستور <b>{name}</b> ذخیره شد.\nاکنون تنظیماتش را انتخاب کن 👇",
        parse_mode="HTML",
        reply_markup=build_panel_keyboard(name, doc["settings"])
    )

# ======================== 📤 اجرا ========================

async def handle_custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    chat_type = update.effective_chat.type
    user = update.effective_user

    commands = load_commands()
    if text not in commands:
        return

    cmd = commands[text]
    settings = cmd.get("settings", {"access": ["everyone"], "targets": ["group", "private"], "mode": "all"})

    # بررسی دسترسی‌ها
    if "admins" in settings["access"]:
        member = await update.effective_chat.get_member(user.id)
        if not (member.status in ["administrator", "creator"] or user.id == ADMIN_ID):
            return await update.message.reply_text("⛔ فقط مدیران اجازه اجرای این دستور را دارند.")

    if chat_type in ["group", "supergroup"] and "group" not in settings["targets"]:
        return
    if chat_type == "private" and "private" not in settings["targets"]:
        return

    responses = cmd.get("responses", [])
    if not responses:
        return await update.message.reply_text("⚠️ هنوز پاسخی برای این دستور ثبت نشده.")

    response = random.choice(responses) if settings.get("mode") == "random" else responses[0]

    try:
        t, d = response["type"], response["data"]
        if t == "text": await update.message.reply_text(d)
        elif t == "photo": await update.message.reply_photo(d)
        elif t == "video": await update.message.reply_video(d)
        elif t == "document": await update.message.reply_document(d)
        elif t == "voice": await update.message.reply_voice(d)
        elif t == "animation": await update.message.reply_animation(d)
        elif t == "sticker": await update.message.reply_sticker(d)
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در اجرای دستور:\n{e}")

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
        await update.message.reply_text("⚠️ چنین دستوری وجود ندارد.")

# ======================== 🎛 پنل ========================

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

    if action == "access":
        target = data[2]
        settings["access"] = [a for a in settings["access"] if a != target] if target in settings["access"] else settings["access"] + [target]
    elif action == "target":
        target = data[2]
        settings["targets"] = [t for t in settings["targets"] if t != target] if target in settings["targets"] else settings["targets"] + [target]
    elif action == "mode":
        settings["mode"] = data[2]
    elif action == "save":
        commands[name]["settings"] = settings
        save_commands(commands)
        return await query.edit_message_text(f"✅ تنظیمات '{name}' ذخیره شد!")
    elif action == "delete":
        del commands[name]
        save_commands(commands)
        return await query.edit_message_text(f"🗑 دستور '{name}' حذف شد!")

    try:
        commands[name]["settings"] = settings
        save_commands(commands)
        await query.edit_message_reply_markup(reply_markup=build_panel_keyboard(name, settings))
    except BadRequest:
        pass
