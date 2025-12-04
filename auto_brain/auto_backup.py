# ======================= ☁️ بک‌آپ خودکار و دستی (نسخه نهایی async) =======================
import os
import zipfile
import shutil
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

# 🧩 تنظیمات پایه
BACKUP_FOLDER = "backups"
ADMIN_ID = int(os.getenv("ADMIN_ID", "8588347189"))

# ======================= 🧠 توابع پایه =======================
def _should_include_in_backup(path: str) -> bool:
    """فقط فایل‌های مهم داخل بک‌آپ بروند"""
    lowered = path.lower()
    skip_dirs = ["__pycache__", ".git", "venv", "restore_temp", BACKUP_FOLDER]

    # پوشه‌هایی که نباید بک‌آپ شوند
    if any(sd in lowered for sd in skip_dirs):
        return False

    # ZIP ها و بک‌آپ‌های قبلی
    if lowered.endswith(".zip") or os.path.basename(lowered).startswith("backup_"):
        return False

    # فایل مهم سفارشی
    if os.path.basename(path) in ["custom_commands.json", "custom_commands_backup.json"]:
        return True

    # فایل‌های مهم عمومی
    important_files = [
        "data/groups.json",
        "data/users.json",
        "jokes.json",
        "fortunes.json",
        "data/custom_commands.json",
        "fortunes_media",
    ]

    if any(path.endswith(f) or f in path for f in important_files):
        return True

    # انواع مدیا
    return lowered.endswith((".json", ".jpg", ".png", ".webp", ".mp3", ".ogg"))

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

            # 📌 فایل‌های مهم که باید همیشه اضافه شوند
            important_files_extra = [
                "data/groups.json",
                "data/users.json",
                "fortunes.json",
                "jokes.json",
                "fortunes_media",
                "group_control/aliases.json",
                "aliases.json",
                "data/custom_commands.json",
                "custom_commands_backup.json"
            ]

            for imp in important_files_extra:
                if os.path.exists(imp):
                    if os.path.isdir(imp):
                        for root, _, files in os.walk(imp):
                            for file in files:
                                full_path = os.path.join(root, file)
                                arcname = os.path.relpath(full_path, ".")
                                zipf.write(full_path, arcname)
                    else:
                        zipf.write(imp, imp)

            # 🔍 اضافه کردن فایل‌های مهم از کل پروژه
            for root, _, files in os.walk("."):
                for file in files:
                    full_path = os.path.join(root, file)
                    if _should_include_in_backup(full_path):
                        arcname = os.path.relpath(full_path, ".")
                        zipf.write(full_path, arcname)

        # ارسال فایل
        size_mb = os.path.getsize(filename) / (1024 * 1024)

        caption = (
            f"🧠 <b>بک‌آپ جدید ساخته شد!</b>\n"
            f"📅 تاریخ: <code>{now}</code>\n"
            f"💾 حجم: <code>{size_mb:.2f} MB</code>\n"
            f"☁️ نوع: {reason}"
        )

        with open(filename, "rb") as f:
            await bot.send_document(chat_id=ADMIN_ID, document=f, caption=caption, parse_mode="HTML")

    except Exception as e:
        print(f"[CLOUD BACKUP ERROR] {e}")
        try:
            await bot.send_message(chat_id=ADMIN_ID, text=f"⚠️ خطا:\n{e}")
        except:
            pass

    finally:
        if os.path.exists(filename):
            os.remove(filename)

# ======================= 💬 دستور /cloudsync =======================
async def cloudsync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")
    await cloudsync_internal(context.bot, "Manual Cloud Backup")

# ======================= 💾 بک‌آپ و بازیابی ZIP =======================
async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cloudsync_internal(context.bot, "Manual Backup")
    await update.message.reply_text("✅ بک‌آپ کامل گرفته شد!")

async def restore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📂 فایل ZIP بک‌آپ را ارسال کن.")
    context.user_data["await_restore"] = True

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("await_restore"):
        return

    doc = update.message.document
    if not doc or not doc.file_name.lower().endswith(".zip"):
        return await update.message.reply_text("❗ فقط فایل ZIP معتبر بفرست.")

    restore_zip = "restore.zip"
    restore_dir = "restore_temp"

    try:
        tg_file = await doc.get_file()
        await tg_file.download_to_drive(restore_zip)

        if os.path.exists(restore_dir):
            shutil.rmtree(restore_dir)
        os.makedirs(restore_dir)

        with zipfile.ZipFile(restore_zip, "r") as zip_ref:
            zip_ref.extractall(restore_dir)

        # 🧩 فایل‌هایی که باید بازیابی شوند
        important_files = [
            "data/groups.json",
            "data/users.json",
            "jokes.json",
            "fortunes.json",
            "fortunes_media",
            "aliases.json",
            "group_control/aliases.json",
            "data/custom_commands.json",
        ]

        moved_any = False
        for fname in important_files:
            src = os.path.join(restore_dir, fname)
            dest = fname

            if os.path.exists(src):
                if os.path.isdir(src):
                    if os.path.exists(dest):
                        shutil.rmtree(dest)
                    shutil.copytree(src, dest)
                else:
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    shutil.move(src, dest)

                moved_any = True

        if moved_any:
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
