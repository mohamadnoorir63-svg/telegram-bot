# ==================== ⚙️ command_panel.py ====================
import json
import os
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes

COMMANDS_FILE = "auto_brain/commands_data.json"
ADMIN_ID = 7089376754

# ------------------- 🧩 توابع کمکی -------------------

def load_commands():
    if os.path.exists(COMMANDS_FILE):
        with open(COMMANDS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_commands(data):
    with open(COMMANDS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ------------------- 📋 ساخت پنل تنظیمات -------------------

async def show_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پنل تنظیمات برای دستور خاص"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")

    if not context.args:
        return await update.message.reply_text("❗ فرمت درست: /panel <نام دستور>")

    name = " ".join(context.args).strip().lower()
    commands = load_commands()
    cmd = commands.get(name)

    if not cmd:
        return await update.message.reply_text("⚠️ این دستور هنوز وجود ندارد.")

    settings = cmd.get("settings", {"access": ["everyone"], "mode": "all"})
    await update.message.reply_text(
        f"شما اکنون در حال تنظیم دستور <b>{name}</b> هستید ⚙️\n\n"
        "- انتخاب کنید چه کسانی بتوانند این دستور را اجرا کنند.\n"
        "- مشخص کنید که همهٔ پاسخ‌ها باهم ارسال شوند یا یکی تصادفی.\n\n"
        "گزینه‌های فعال با ✅ مشخص شده‌اند.",
        reply_markup=_panel_keyboard(name, settings),
        parse_mode="HTML"
    )

# ------------------- 🎛 ساخت دکمه‌ها -------------------

def _panel_keyboard(name, settings):
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
            InlineKeyboardButton(f"{mode_check('all')} ارسال برای همه", callback_data=f"mode:{name}:all"),
            InlineKeyboardButton(f"{mode_check('random')} تصادفی", callback_data=f"mode:{name}:random"),
        ],
        [
            InlineKeyboardButton("💾 ذخیره", callback_data=f"save:{name}"),
            InlineKeyboardButton("🗑 حذف", callback_data=f"del:{name}"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# ------------------- 🔄 مدیریت کلیک دکمه‌ها -------------------

async def panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت دکمه‌ها"""
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
        target = data[2]
        settings["mode"] = target

    elif action == "save":
        cmd["settings"] = settings
        commands[name] = cmd
        save_commands(commands)
        return await query.edit_message_text(f"✅ تنظیمات برای '{name}' ذخیره شد!")

    elif action == "del":
        del commands[name]
        save_commands(commands)
        return await query.edit_message_text(f"🗑 دستور '{name}' حذف شد!")

    # در غیر این صورت فقط دکمه‌ها را به‌روز کن
    cmd["settings"] = settings
    commands[name] = cmd
    save_commands(commands)

    try:
        await query.edit_message_reply_markup(reply_markup=_panel_keyboard(name, settings))
    except:
        await query.edit_message_text(f"✅ تغییرات اعمال شد برای '{name}'")
