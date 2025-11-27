# ======================= ☁️ بک‌آپ خودکار و دستی (نسخه نهایی async) =======================
import os
import zipfile
import shutil
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
import json

# 🧩 تنظیمات پایه
BACKUP_FOLDER = "backups"
ADMIN_ID = int(os.getenv("ADMIN_ID", "8588347189"))

# ======================= 🧠 بازسازی فایل‌های پایه =======================
def init_files():
    """بازسازی فایل‌های پایه در صورت عدم وجود"""
    base_files = [
        "group_data.json",
        "users.json",
        "data/custom_commands.json",
        "jokes.json",
        "fortunes.json"
    ]
    for f in base_files:
        dir_name = os.path.dirname(f)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
        if not os.path.exists(f):
            with open(f, "w", encoding="utf-8") as fp:
                json.dump({} if f != "users.json" else [], fp, ensure_ascii=False, indent=2)

# ======================= ⚙️ تعیین فایل‌های مهم برای بک‌آپ =======================
def _should_include_in_backup(path: str) -> bool:
    lowered = path.lower()
    skip_dirs = ["__pycache__", ".git", "venv", "restore_temp", BACKUP_FOLDER]

    if any(sd in lowered for sd in skip_dirs):
        return False
    if lowered.endswith(".zip") or os.path.basename(lowered).startswith("backup_"):
        return False

    important_files = [
        "group_data.json",
        "users.json",
        "jokes.json",
        "fortunes.json",
        "data/custom_commands.json",
        "fortunes_media",
    ]
    return any(path.endswith(f) or f in path for f in important_files) or lowered.endswith((".jpg", ".png", ".webp", ".mp3", ".ogg"))

# ======================= ☁️ بک‌آپ خودکار =======================
async def auto_backup(bot):
    while True:
        await cloudsync_internal(bot, "Auto Backup")
        await asyncio.sleep(6 * 60 * 60)

# ======================= 💾 ساخت و ارسال بک‌آپ =======================
async def cloudsync_internal(bot, reason="Manual Backup"):
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"backup_{now}.zip"

    try:
        with zipfile.ZipFile(filename, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
            important_files_extra = [
                "group_data.json",
                "users.json",
                "jokes.json",
                "fortunes.json",
                "fortunes_media",
                "data/custom_commands.json"
            ]
            for imp in important_files_extra:
                if os.path.exists(imp):
                    if os.path.isdir(imp):
                        for root, _, files in os.walk(imp):
                            for file in files:
                                full_path = os.path.join(root, file)
                                arcname = os.path.relpath(full_path, ".")
                                zipf.write(full_path, arcname=arcname)
                    else:
                        zipf.write(imp)

            for root, _, files in os.walk("."):
                for file in files:
                    full_path = os.path.join(root, file)
                    if _should_include_in_backup(full_path):
                        arcname = os.path.relpath(full_path, ".")
                        zipf.write(full_path, arcname=arcname)

        size_mb = os.path.getsize(filename) / (1024 * 1024)
        caption = (
            f"🧠 <b>بک‌آپ جدید ساخته شد!</b>\n"
            f"📅 تاریخ: <code>{now}</code>\n"
            f"💾 حجم: <code>{size_mb:.2f} MB</code>\n"
            f"☁️ نوع: {reason}"
        )

        with open(filename, "rb") as f:
            await bot.send_document(chat_id=ADMIN_ID, document=f, caption=caption, parse_mode="HTML")

    finally:
        if os.path.exists(filename):
            os.remove(filename)

# ======================= 💬 دستور /cloudsync =======================
async def cloudsync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")
    await cloudsync_internal(context.bot, "Manual Cloud Backup")

# ======================= 💾 بک‌آپ و بازیابی در چت =======================
async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cloudsync_internal(context.bot, "Manual Backup")
    await update.message.reply_text("✅ بک‌آپ کامل گرفته شد و ارسال شد!")

async def restore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📂 لطفاً فایل ZIP بک‌آپ را ارسال کنید.")
    context.user_data["await_restore"] = True

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("await_restore"):
        return

    doc = update.message.document
    if not doc or not doc.file_name.lower().endswith(".zip"):
        return await update.message.reply_text("❗ لطفاً فقط فایل ZIP معتبر ارسال کنید.")

    restore_zip = "restore.zip"
    restore_dir = "restore_temp"

    try:
        tg_file = await doc.get_file()
        await tg_file.download_to_drive(restore_zip)

        if os.path.exists(restore_dir):
            shutil.rmtree(restore_dir)
        os.makedirs(restore_dir, exist_ok=True)

        with zipfile.ZipFile(restore_zip, "r") as zip_ref:
            zip_ref.extractall(restore_dir)

        important_files = [
            "group_data.json",
            "users.json",
            "jokes.json",
            "fortunes.json",
            "fortunes_media",
            "data/custom_commands.json"
        ]

        moved_any = False
        for fname in important_files:
            src = os.path.join(restore_dir, fname)
            dest = fname
            dest_dir = os.path.dirname(dest)

            if os.path.exists(src):
                try:
                    if os.path.isdir(src):
                        if os.path.exists(dest):
                            shutil.rmtree(dest)
                        shutil.copytree(src, dest)
                    else:
                        if dest_dir and not os.path.exists(dest_dir):
                            os.makedirs(dest_dir, exist_ok=True)
                        shutil.move(src, dest)
                    moved_any = True
                except Exception as e:
                    print(f"⚠️ خطا در بازیابی فایل {fname}: {e}")

        # بازسازی فایل‌های پایه در صورت عدم وجود
        init_files()

        if moved_any:
            await update.message.reply_text("✅ بازیابی کامل انجام شد!")
        else:
            await update.message.reply_text("ℹ️ فایلی برای جایگزینی پیدا نشد.")

    finally:
        if os.path.exists(restore_zip):
            os.remove(restore_zip)
        if os.path.exists(restore_dir):
            shutil.rmtree(restore_dir)
        context.user_data["await_restore"] = False
