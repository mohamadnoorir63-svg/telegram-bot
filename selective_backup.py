# ====================== 🎛 بک‌آپ انتخابی (فقط برای سودو) ======================
import os
import zipfile
import io
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ContextTypes, CallbackQueryHandler

# فایل‌هایی که میشه بک‌آپ گرفت
BACKUP_TARGETS = {
    "memory.json": "🧠 حافظه اصلی",
    "shadow_memory.json": "👥 حافظه سایه",
    "group_data.json": "👥 داده‌های گروه‌ها",
    "users.json": "👤 کاربران",
    "fortunes.json": "🔮 فال‌ها",
    "jokes_manager.py": "😂 جوک‌ها",
    "custom_help.txt": "📘 راهنمای سفارشی",
}

# مسیر بک‌آپ‌ها
BACKUP_DIR = os.path.join(os.path.dirname(__file__), "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

# آیدی سودو (سازنده)
ADMIN_ID = int(os.getenv("ADMIN_ID", "7089376754"))


# شروع فرآیند انتخاب بک‌آپ
async def selective_backup_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """منوی انتخاب فایل‌ها برای بک‌آپ (فقط برای سودو)"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 فقط سودو می‌تونه از این دستور استفاده کنه.")

    keyboard = [
        [InlineKeyboardButton(f"{icon} {name}", callback_data=f"selbk_{key}")]
        for key, name in BACKUP_TARGETS.items()
    ]
    keyboard.append([InlineKeyboardButton("✅ انجام بک‌آپ", callback_data="selbk_do")])
    keyboard.append([InlineKeyboardButton("❌ لغو", callback_data="selbk_cancel")])

    context.user_data["selected_files"] = set()

    await update.message.reply_text(
        "📦 لطفاً فایل‌هایی که می‌خوای بک‌آپ بگیری انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# مدیریت انتخاب دکمه‌ها
async def selective_backup_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    selected = context.user_data.get("selected_files", set())

    # لغو
    if data == "selbk_cancel":
        context.user_data.pop("selected_files", None)
        return await query.edit_message_text("❌ عملیات بک‌آپ لغو شد.")

    # انجام بک‌آپ
    if data == "selbk_do":
        if not selected:
            return await query.edit_message_text("⚠️ هیچ فایلی انتخاب نشده بود!")

        zip_buffer = io.BytesIO()
        zip_name = f"backup_selected_{len(selected)}files.zip"

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file in selected:
                if os.path.exists(file):
                    zipf.write(file)
                else:
                    print(f"[⚠️ فایل یافت نشد]: {file}")

        zip_buffer.seek(0)
        zip_path = os.path.join(BACKUP_DIR, zip_name)
        with open(zip_path, "wb") as f:
            f.write(zip_buffer.read())

        # ارسال بک‌آپ برای سودو
        await query.message.reply_document(
            document=InputFile(zip_path),
            caption=f"✅ بک‌آپ از {len(selected)} فایل با موفقیت ساخته شد.",
        )

        return await query.edit_message_text("📦 بک‌آپ ارسال شد ✅")

    # انتخاب/لغو انتخاب فایل‌ها
    if data.startswith("selbk_"):
        key = data.replace("selbk_", "")
        if key in selected:
            selected.remove(key)
        else:
            selected.add(key)
        context.user_data["selected_files"] = selected

        # بروزرسانی متن
        text = "📦 فایل‌های انتخاب‌شده:\n"
        if not selected:
            text += "هیچ فایلی انتخاب نشده 😅"
        else:
            text += "\n".join([f"✅ {BACKUP_TARGETS.get(f, f)}" for f in selected])

        keyboard = [
            [InlineKeyboardButton(
                ("☑️ " if k in selected else "⬜️ ") + BACKUP_TARGETS[k],
                callback_data=f"selbk_{k}")
             ]
            for k in BACKUP_TARGETS
        ]
        keyboard.append([InlineKeyboardButton("✅ انجام بک‌آپ", callback_data="selbk_do")])
        keyboard.append([InlineKeyboardButton("❌ لغو", callback_data="selbk_cancel")])

        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard)
  )
