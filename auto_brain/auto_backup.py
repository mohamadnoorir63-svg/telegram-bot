# ======================= ☁️ Backup & Restore — Final Stable Version =======================
import os
import zipfile
import shutil
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

# تنظیمات
BACKUP_FOLDER = "backups"
ADMIN_ID = int(os.getenv("ADMIN_ID", "8588347189"))

# ======================= 🧠 تعیین فایل‌های مهم =======================
IMPORTANT_FILES = [
    "data/groups.json",
    "data/users.json",
    "jokes.json",
    "fortunes.json",
    "data/custom_commands.json",
    "fortunes_media",
    "backup/dynamic_buttons/buttons.json",
    "group_control/aliases.json",
    "aliases.json",
    "custom_commands_backup.json"
]

def _should_include_in_backup(path: str) -> bool:
    """فقط فایل‌ها و فولدرهای مهم در بک‌آپ قرار بگیرند"""
    lowered = path.lower()
    skip_dirs = ["__pycache__", ".git", "venv", "restore_temp", BACKUP_FOLDER]

    if any(sd in lowered for sd in skip_dirs):
        return False

    if lowered.endswith(".zip") or os.path.basename(lowered).startswith("backup_"):
        return False

    # اگر فایل در لیست مهم‌ها بود
    if any(path.endswith(f) or f in path for f in IMPORTANT_FILES):
        return True

    # فایل‌های رسانه‌ای/متنی
    return lowered.endswith((".json", ".jpg", ".png", ".webp", ".mp3", ".ogg"))

# ======================= ☁️ Auto Backup =======================
async def auto_backup(bot):
    while True:
        await cloudsync_internal(bot, "Auto Backup")
        await asyncio.sleep(6 * 60 * 60)

# ======================= 💾 ساخت ZIP و ارسال =======================
async def cloudsync_internal(bot, reason="Manual Backup"):
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"backup_{now}.zip"

    try:
        with zipfile.ZipFile(filename, "w", compression=zipfile.ZIP_DEFLATED) as zipf:

            # اضافه‌کردن فایل‌های ضروری
            for imp in IMPORTANT_FILES:
                if os.path.exists(imp):
                    if os.path.isdir(imp):
                        for root, _, files in os.walk(imp):
                            for f in files:
                                full_path = os.path.join(root, f)
                                arcname = os.path.relpath(full_path, ".")
                                zipf.write(full_path, arcname)
                    else:
                        zipf.write(imp, imp)

            # بررسی کل پروژه
            for root, _, files in os.walk("."):
                for f in files:
                    full_path = os.path.join(root, f)
                    if _should_include_in_backup(full_path):
                        arcname = os.path.relpath(full_path, ".")
                        zipf.write(full_path, arcname)

        # ارسال فایل به مدیر
        size_mb = os.path.getsize(filename) / (1024 * 1024)
        caption = (
            f"🧠 <b>بک‌آپ ساخته شد!</b>\n"
            f"📅 <code>{now}</code>\n"
            f"💾 <code>{size_mb:.2f} MB</code>\n"
            f"☁️ نوع: {reason}"
        )

        with open(filename, "rb") as f:
            await bot.send_document(ADMIN_ID, f, caption=caption, parse_mode="HTML")

    except Exception as e:
        print(f"[BACKUP ERROR] {e}")
        try:
            await bot.send_message(ADMIN_ID, f"⚠️ خطا در بک‌آپ:\n{e}")
        except:
            pass
    finally:
        if os.path.exists(filename):
            os.remove(filename)

# ======================= 💬 /cloudsync =======================
async def cloudsync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")
    await cloudsync_internal(context.bot, "Manual Backup")

# ======================= 💾 /backup =======================
async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cloudsync_internal(context.bot, "Manual Backup")
    await update.message.reply_text("✅ بک‌آپ کامل گرفته شد!")

# ======================= 🔄 /restore =======================
async def restore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📂 فایل ZIP بک‌آپ را ارسال کنید.")
    context.user_data["await_restore"] = True

# ======================= 📂 پردازش فایل ZIP =======================
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("await_restore"):
        return

    doc = update.message.document
    if not doc or not doc.file_name.lower().endswith(".zip"):
        return await update.message.reply_text("⚠️ فقط ZIP معتبر ارسال کنید.")

    restore_zip = "restore.zip"
    restore_dir = "restore_temp"

    try:
        tg_file = await doc.get_file()
        await tg_file.download_to_drive(restore_zip)

        if os.path.exists(restore_dir):
            shutil.rmtree(restore_dir)
        os.makedirs(restore_dir)

        with zipfile.ZipFile(restore_zip, "r") as z:
            z.extractall(restore_dir)

        moved = False
        for fname in IMPORTANT_FILES:
            src = os.path.join(restore_dir, fname)
            dest = fname

            if os.path.exists(src):
                os.makedirs(os.path.dirname(dest), exist_ok=True)

                if os.path.isdir(src):
                    if os.path.exists(dest):
                        shutil.rmtree(dest)
                    shutil.copytree(src, dest)
                else:
                    shutil.move(src, dest)

                moved = True

        if moved:
            await update.message.reply_text("✅ بازیابی کامل انجام شد!")
        else:
            await update.message.reply_text("ℹ️ هیچ فایل مهمی پیدا نشد!")

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در بازیابی:\n{e}")

    finally:
        if os.path.exists(restore_zip):
            os.remove(restore_zip)
        if os.path.exists(restore_dir):
            shutil.rmtree(restore_dir)
        context.user_data["await_restore"] = False
