# ====================== 🎛 بک‌آپ انتخابی و معتبر ======================
import os
import zipfile
import io
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ContextTypes

# ====================== ⚙️ تنظیمات پایه ======================
ADMIN_ID = int(os.getenv("ADMIN_ID", "8588347189)
BACKUP_DIR = os.path.join(os.path.dirname(__file__), "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

# 🎨 آیکون‌ها
ICONS = {
    "memory.json": "🧠",
    "shadow_memory.json": "👥",
    "group_data.json": "💬",
    "users.json": "👤",
    "custom_commands.json": "📜",
    "custom_commands_backup.json": "🗄️",
    "fortunes_media": "🖼️",
    "fortunes.json": "🔮",
    "jokes_manager.py": "😂",
    "custom_help.txt": "📘",
    "group_control/aliases.json": "🧩",
}

# 📦 فایل‌هایی که میشه بک‌آپ گرفت
BACKUP_TARGETS = {
    "memory.json": "حافظه اصلی",
    "shadow_memory.json": "حافظه سایه",
    "custom_commands.json": "دستورهای ذخیره‌شده",
    "custom_commands_backup.json": "بک‌آپ دستورها",
    "group_data.json": "داده‌های گروه‌ها",
    "users.json": "کاربران",
    "fortunes.json": "فال‌ها",
    "jokes_manager.py": "جوک‌ها",
    "custom_help.txt": "راهنمای سفارشی",
    "group_control/aliases.json": "دستورات سفارشی (alias)",
}

# ====================== 📋 منوی انتخاب فایل‌ها ======================
async def selective_backup_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 فقط سودو می‌تونه از این دستور استفاده کنه.")

    context.user_data["selected_files"] = set()
    keyboard = [
        [InlineKeyboardButton(f"{ICONS.get(key, '📁')} {name}", callback_data=f"selbk_{key}")]
        for key, name in BACKUP_TARGETS.items()
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

        zip_buffer = io.BytesIO()
        zip_name = f"backup_selected_{len(selected)}files.zip"

        try:
            # ایجاد ZIP در حافظه
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
                for file in selected:
                    if os.path.isfile(file):
                        zipf.write(file, arcname=os.path.basename(file))
                        print(f"📁 افزودن فایل انتخابی: {file}")
                    else:
                        print(f"[⚠️ فایل یافت نشد یا پوشه است]: {file}")

            zip_buffer.seek(0)

            # ارسال مستقیم به تلگرام بدون ذخیره روی دیسک
            await query.message.reply_document(
                document=InputFile(zip_buffer, filename=zip_name),
                caption=f"✅ بک‌آپ از {len(selected)} فایل با موفقیت ساخته شد!",
            )

            return await query.edit_message_text("📦 فایل بک‌آپ ارسال شد ✅")

        except Exception as e:
            return await query.edit_message_text(f"⚠️ خطا در ساخت بک‌آپ: {e}")

    # ☑️ انتخاب یا لغو انتخاب فایل‌ها
    if data.startswith("selbk_"):
        key = data.replace("selbk_", "")
        if key in selected:
            selected.remove(key)
        else:
            selected.add(key)
        context.user_data["selected_files"] = selected

        # بروزرسانی منو
        text = "📦 فایل‌های انتخاب‌شده:\n"
        if not selected:
            text += "هیچ فایلی انتخاب نشده 😅"
        else:
            text += "\n".join([f"✅ {BACKUP_TARGETS.get(f, f)}" for f in selected])

        keyboard = [
            [InlineKeyboardButton(
                ("☑️ " if k in selected else "⬜️ ") + f"{ICONS.get(k, '📁')} {BACKUP_TARGETS[k]}",
                callback_data=f"selbk_{k}"
            )]
            for k in BACKUP_TARGETS
        ]
        keyboard.append([InlineKeyboardButton("✅ انجام بک‌آپ", callback_data="selbk_do")])
        keyboard.append([InlineKeyboardButton("❌ لغو", callback_data="selbk_cancel")])

        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard)
            )
