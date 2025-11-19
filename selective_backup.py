# ====================== 🎛 بک‌آپ انتخابی و معتبر ======================
import os
import zipfile
import io
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ContextTypes

# ====================== ⚙️ تنظیمات پایه ======================
ADMIN_ID = int(os.getenv("ADMIN_ID", "8588347189"))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

BACKUP_DIR = os.path.join(BASE_DIR, "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

# ====================== مسیرها ======================
MEMORY_FILE = os.path.join(BASE_DIR, "memory.json")
GROUP_DATA_FILE = os.path.join(BASE_DIR, "group_data.json")
JOKES_FILE = os.path.join(BASE_DIR, "jokes.json")
FORTUNES_FILE = os.path.join(BASE_DIR, "fortunes.json")
ALIASES_FILE = os.path.join(BASE_DIR, "aliases.json")

MEMBERS_FILE = os.path.join(DATA_DIR, "members.json")
USERS_FILE = os.path.join(BASE_DIR, "users.json")

CUSTOM_COMMANDS_FILE = os.path.join(DATA_DIR, "custom_commands.json")
CUSTOM_COMMANDS_BACKUP = os.path.join(BASE_DIR, "custom_commands_backup.json")

GROUP_ALIASES_FILE = os.path.join(BASE_DIR, "group_control", "aliases.json")
os.makedirs(os.path.join(BASE_DIR, "group_control"), exist_ok=True)

FORTUNES_MEDIA_DIR = os.path.join(BASE_DIR, "fortunes_media")

ICONS = {
    "memory": "🧠",
    "group_data": "💬",
    "jokes": "😂",
    "fortunes": "🔮",
    "aliases": "🧩",
    "members": "👥",
    "users": "👤",
    "commands": "📜",
    "commands_backup": "🗄️",
    "group_aliases": "🧷",
    "media": "🎞️",
}

BACKUP_TARGETS = {
    "memory": MEMORY_FILE,
    "group_data": GROUP_DATA_FILE,
    "jokes": JOKES_FILE,
    "fortunes": FORTUNES_FILE,
    "aliases": ALIASES_FILE,
    "members": MEMBERS_FILE,
    "users": USERS_FILE,
    "commands": CUSTOM_COMMANDS_FILE,
    "commands_backup": CUSTOM_COMMANDS_BACKUP,
    "group_aliases": GROUP_ALIASES_FILE,
    "media": FORTUNES_MEDIA_DIR,
}

BACKUP_NAMES = {
    "memory": "حافظه",
    "group_data": "اطلاعات گروه",
    "jokes": "جوک‌ها",
    "fortunes": "فال‌ها",
    "aliases": "aliases",
    "members": "اعضای گروه",
    "users": "کاربران",
    "commands": "دستورهای ذخیره‌شده",
    "commands_backup": "بک‌آپ دستورها",
    "group_aliases": "گروه alias ها",
    "media": "رسانه فال‌ها",
}


# ====================== 📋 منوی انتخاب فایل‌ها ======================
async def selective_backup_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 فقط سودو می‌تونه از این دستور استفاده کنه.")

    context.user_data["selected_files"] = set()

    keyboard = [
        [InlineKeyboardButton(
            f"{ICONS[k]} {BACKUP_NAMES[k]}",
            callback_data=f"selbk_{k}"
        )] for k in BACKUP_TARGETS.keys()
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

            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:

                for key in selected:
                    path = BACKUP_TARGETS[key]

                    # اگر پوشه بود → کل مسیر نسبی پوشه را ذخیره کن
                    if os.path.isdir(path):
                        for root, dirs, files in os.walk(path):
                            for file in files:
                                full_path = os.path.join(root, file)

                                # مسیر نسبی درست → تا هنگام restore دقیقاً ایجاد شود
                                rel_path = os.path.relpath(full_path, BASE_DIR)

                                zipf.write(full_path, rel_path)

                        continue

                    # اگر فایل بود
                    if os.path.isfile(path):

                        # مسیر نسبی درست
                        rel_path = os.path.relpath(path, BASE_DIR)

                        zipf.write(path, rel_path)

            zip_buffer.seek(0)

            await query.message.reply_document(
                InputFile(zip_buffer, filename=zip_name),
                caption=f"✅ بک‌آپ از {len(selected)} فایل ساخته شد!"
            )

            return await query.edit_message_text("📦 فایل بک‌آپ ارسال شد.")

        except Exception as e:
            return await query.edit_message_text(f"⚠️ خطا در ساخت ZIP:\n{e}")

    # ☑️ انتخاب/عدم انتخاب
    if data.startswith("selbk_"):
        key = data.replace("selbk_", "")

        if key in selected:
            selected.remove(key)
        else:
            selected.add(key)

        context.user_data["selected_files"] = selected

        text = "📦 فایل‌های انتخاب‌شده:\n"
        text += "\n".join([f"✅ {BACKUP_NAMES[k]}" for k in selected]) if selected else "هیچ فایلی انتخاب نشده 😅"

        keyboard = [
            [InlineKeyboardButton(
                ("☑️ " if k in selected else "⬜️ ") + f"{ICONS[k]} {BACKUP_NAMES[k]}",
                callback_data=f"selbk_{k}"
            )] for k in BACKUP_TARGETS.keys()
        ]
        keyboard.append([InlineKeyboardButton("✅ انجام بک‌آپ", callback_data="selbk_do")])
        keyboard.append([InlineKeyboardButton("❌ لغو", callback_data="selbk_cancel")])

        return await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
