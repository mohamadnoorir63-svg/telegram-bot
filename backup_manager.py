# ======================= ☁️ NOORI Backup Manager v10.2 (Stable) =======================
import os
import zipfile
import shutil
import asyncio
from datetime import datetime
from telegram import InputFile, Update
from telegram.ext import ContextTypes

# 📦 مسیر پوشه بک‌آپ‌ها
BACKUP_DIR = "backups"
os.makedirs(BACKUP_DIR, exist_ok=True)

# 📄 فایل‌های مهم برای بازیابی
IMPORTANT_FILES = [
    "memory.json",
    "group_data.json",
    "jokes.json",
    "fortunes.json",
    "warnings.json",
    "aliases.json",
]

# 🎯 انتخاب فایل‌هایی که باید داخل بک‌آپ بروند
def _should_include_in_backup(path: str) -> bool:
    skip_dirs = ["__pycache__", ".git", "venv", "restore_temp", "backups"]
    lowered = path.lower()
    if any(sd in lowered for sd in skip_dirs):
        return False
    if lowered.endswith(".zip"):
        return False
    return lowered.endswith((".json", ".jpg", ".png", ".webp", ".mp3", ".ogg"))

# 🧩 ایجاد فایل ZIP بک‌آپ
def create_backup_zip():
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"backup_{now}.zip"
    zip_path = os.path.join(BACKUP_DIR, filename)

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk("."):
            for file in files:
                full_path = os.path.join(root, file)
                if _should_include_in_backup(full_path):
                    arcname = os.path.relpath(full_path, ".")
                    zipf.write(full_path, arcname=arcname)

    return zip_path, now

# 💾 بک‌آپ دستی (با دستور /backup)
async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ایجاد بک‌آپ دستی و ارسال در چت"""
    ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")

    zip_path, timestamp = create_backup_zip()
    try:
        await update.message.reply_document(InputFile(zip_path))
        await update.message.reply_text(f"✅ بک‌آپ دستی انجام شد!\n🕓 {timestamp}")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در ارسال بک‌آپ:\n{e}")
    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)

# ☁️ بک‌آپ ابری (با دستور /cloudsync)
async def cloudsync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال بک‌آپ به ادمین به صورت ابری"""
    ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")

    zip_path, timestamp = create_backup_zip()
    try:
        await context.bot.send_document(chat_id=ADMIN_ID, document=InputFile(zip_path))
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"☁️ Cloud Backup — {timestamp}")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در Cloud Backup:\n{e}")
    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)

# ♻️ بازیابی فایل ZIP (با دستور /restore)
async def restore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بازیابی بک‌آپ با نوار پیشرفت"""
    ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه بازیابی کنه!")

    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        return await update.message.reply_text("📎 فایل ZIP بک‌آپ را ریپلای کن و بعد دستور /restore بزن.")

    file = await update.message.reply_to_message.document.get_file()
    zip_path = os.path.join(BACKUP_DIR, "restore_temp.zip")
    await file.download_to_drive(zip_path)

    msg = await update.message.reply_text("♻️ شروع بازیابی...\n0% [▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒]")
    restore_dir = "restore_temp"

    if os.path.exists(restore_dir):
        shutil.rmtree(restore_dir)
    os.makedirs(restore_dir, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            files = zip_ref.namelist()
            total = len(files)
            for i, file in enumerate(files, start=1):
                zip_ref.extract(file, restore_dir)
                percent = int(i / total * 100)
                bars = int(percent / 5)
                progress_bar = "█" * bars + "▒" * (20 - bars)
                await msg.edit_text(f"♻️ بازیابی {percent}% [{progress_bar}]")
                await asyncio.sleep(0.1)

        moved = 0
        for f in IMPORTANT_FILES:
            src = os.path.join(restore_dir, f)
            if os.path.exists(src):
                shutil.move(src, f)
                moved += 1

        await msg.edit_text(f"✅ بازیابی کامل شد!\n📦 {moved} فایل بازگردانی گردید.\n🤖 سیستم آماده است.")

    except Exception as e:
        await msg.edit_text(f"⚠️ خطا در بازیابی:\n{e}")

    finally:
        if os.path.exists(restore_dir):
            shutil.rmtree(restore_dir)
        if os.path.exists(zip_path):
            os.remove(zip_path)

# 🔁 بک‌آپ خودکار هر ۶ ساعت
async def auto_backup(bot):
    """ارسال بک‌آپ خودکار هر ۶ ساعت به ادمین"""
    ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
    while True:
        try:
            zip_path, timestamp = create_backup_zip()
            await bot.send_document(chat_id=ADMIN_ID, document=InputFile(zip_path))
            await bot.send_message(chat_id=ADMIN_ID, text=f"🤖 Auto Backup — {timestamp}")
            print(f"[AUTO BACKUP] {timestamp} sent ✅")
        except Exception as e:
            print(f"[AUTO BACKUP ERROR] {e}")
        finally:
            if os.path.exists(zip_path):
                os.remove(zip_path)
        await asyncio.sleep(21600)  # هر 6 ساعت
