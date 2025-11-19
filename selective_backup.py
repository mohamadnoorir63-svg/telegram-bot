# ====================== 🎛 بک‌آپ انتخابی و معتبر ======================
import os
import zipfile
import io
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ContextTypes

# ====================== ⚙️ تنظیمات پایه ======================
ADMIN_ID = int(os.getenv("ADMIN_ID", "8588347189"))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# مسیر پوشه data کنار bot.py
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# پوشه بک‌آپ
BACKUP_DIR = os.path.join(BASE_DIR, "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

# مسیر فایل‌ها
CUSTOM_COMMANDS_FILE = os.path.join(DATA_DIR, "custom_commands.json")
CUSTOM_COMMANDS_BACKUP = os.path.join(DATA_DIR, "custom_commands_backup.json")
MEMORY_FILE = os.path.join(DATA_DIR, "memory.json")
SHADOW_MEMORY_FILE = os.path.join(DATA_DIR, "shadow_memory.json")
GROUP_DATA_FILE = os.path.join(DATA_DIR, "group_data.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
FORTUNES_FILE = os.path.join(DATA_DIR, "fortunes.json")
CUSTOM_HELP_FILE = os.path.join(DATA_DIR, "custom_help.txt")
GROUP_ALIASES_FILE = os.path.join(DATA_DIR, "group_control", "aliases.json")
JOKES_FILE = os.path.join(BASE_DIR, "jokes_manager.py")
os.makedirs(os.path.join(DATA_DIR, "group_control"), exist_ok=True)

# 🎨 آیکون‌ها
ICONS = {
    "memory": "🧠",
    "shadow_memory": "👥",
    "group_data": "💬",
    "users": "👤",
    "commands": "📜",
    "commands_backup": "🗄️",
    "fortunes": "🔮",
    "jokes": "😂",
    "help": "📘",
    "aliases": "🧩",
}

# 📦 فایل‌هایی که میشه بک‌آپ گرفت (کلیدهای امن بدون / برای callback_data)
BACKUP_TARGETS = {
    "memory": MEMORY_FILE,
    "shadow_memory": SHADOW_MEMORY_FILE,
    "commands": CUSTOM_COMMANDS_FILE,
    "commands_backup": CUSTOM_COMMANDS_BACKUP,
    "group_data": GROUP_DATA_FILE,
    "users": USERS_FILE,
    "fortunes": FORTUNES_FILE,
    "jokes": JOKES_FILE,
    "help": CUSTOM_HELP_FILE,
    "aliases": GROUP_ALIASES_FILE,
}

# نام نمایشی هر فایل
BACKUP_NAMES = {
    "memory": "حافظه اصلی",
    "shadow_memory": "حافظه سایه",
    "commands": "دستورهای ذخیره‌شده",
    "commands_backup": "بک‌آپ دستورها",
    "group_data": "داده‌های گروه‌ها",
    "users": "کاربران",
    "fortunes": "فال‌ها",
    "jokes": "جوک‌ها",
    "help": "راهنمای سفارشی",
    "aliases": "alias ها",
}


# ====================== 📋 منوی انتخاب فایل‌ها ======================
async def selective_backup_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 فقط سودو می‌تونه از این دستور استفاده کنه.")

    context.user_data["selected_files"] = set()

    keyboard = [
        [InlineKeyboardButton(
            f"{ICONS[key]} {BACKUP_NAMES[key]}",
            callback_data=f"selbk_{key}"
        )]
        for key in BACKUP_TARGETS.keys()
    ]

    keyboard.append([InlineKeyboardButton("✅ انجام بک‌آپ", callback_data="selbk_do")])
    keyboard.append([InlineKeyboardButton("❌ لغو", callback_data="selbk_cancel")])

    await update.message.reply_text(
        "📦 لطفاً فایل‌هایی که می‌خوای بک‌آپ بگیری انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ====================== 🧩 مدیریت دکمه‌ها ======================
async def selective_backup_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    selected = context.user_data.get("selected_files", set())

    # ❌ لغو
    if data == "selbk_cancel":
        context.user_data.pop("selected_files", None)
        return await query.edit_message_text("❌ عملیات بک‌آپ لغو شد.")

    # ✅ انجام بک‌آپ
    if data == "selbk_do":
        if not selected:
            return await query.edit_message_text("⚠️ هیچ فایلی انتخاب نشده بود!")

        try:
            zip_buffer = io.BytesIO()
            zip_name = f"backup_selected_{len(selected)}files.zip"

            # ساخت ZIP
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
                for key in selected:
                    path = BACKUP_TARGETS[key]
                    if os.path.isfile(path):
                        zipf.write(path, os.path.basename(path))
                        print(f"📁 افزودن فایل: {path}")
                    else:
                        print(f"⚠️ فایل یافت نشد: {path}")

            zip_buffer.seek(0)

            # ارسال ZIP
            await query.message.reply_document(
                InputFile(zip_buffer, filename=zip_name),
                caption=f"✅ بک‌آپ از {len(selected)} فایل ساخته شد!"
            )

            return await query.edit_message_text("📦 فایل بک‌آپ ارسال شد.")

        except Exception as e:
            return await query.edit_message_text(f"⚠️ خطا در ساخت بک‌آپ: {e}")

    # ☑️ انتخاب یا لغو انتخاب هر فایل
    if data.startswith("selbk_"):
        key = data.replace("selbk_", "")

        if key in selected:
            selected.remove(key)
        else:
            selected.add(key)

        context.user_data["selected_files"] = selected

        # بروزرسانی منو
        text = "📦 فایل‌های انتخاب‌شده:\n"
        if selected:
            text += "\n".join([f"✅ {BACKUP_NAMES[k]}" for k in selected])
        else:
            text += "هیچ فایلی انتخاب نشده 😅"

        keyboard = [
            [InlineKeyboardButton(
                ("☑️ " if k in selected else "⬜️ ")
                + f"{ICONS[k]} {BACKUP_NAMES[k]}",
                callback_data=f"selbk_{k}"
            )]
            for k in BACKUP_TARGETS.keys()
        ]

        keyboard.append([InlineKeyboardButton("✅ انجام بک‌آپ", callback_data="selbk_do")])
        keyboard.append([InlineKeyboardButton("❌ لغو", callback_data="selbk_cancel")])

        return await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
