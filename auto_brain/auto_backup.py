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
    
    # ۱. بررسی پوشه‌هایی که نباید شامل شوند
    if any(sd in lowered for sd in skip_dirs):
        return False
    
    # ۲. بررسی فایل‌های ZIP یا فایل‌های بک‌آپ خودکار
    if lowered.endswith(".zip") or os.path.basename(lowered).startswith("backup_"):
        return False
    
    # ۳. حتما فایل‌های دستورات ریپلی شامل شوند
    if os.path.basename(path) in ["custom_commands.json", "custom_commands_backup"]:
        return True
    
    # ۴. فایل‌های مهم دیگر بر اساس پسوند
    return lowered.endswith((".json", ".jpg", ".png", ".webp", ".mp3", ".ogg"))

# ======================= ☁️ بک‌آپ خودکار =======================
async def auto_backup(bot):
    """بک‌آپ خودکار هر ۶ ساعت"""
    while True:
        await cloudsync_internal(bot, "Auto Backup")
        await asyncio.sleep(6 * 60 * 60)  # ⏰ هر ۶ ساعت

# ======================= 💾 ساخت و ارسال بک‌آپ =======================
async def cloudsync_internal(bot, reason="Manual Backup"):
    """ایجاد و ارسال فایل ZIP به ادمین"""
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"backup_{now}.zip"

    try:
        with zipfile.ZipFile(filename, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
            # 🧩 افزودن مسیرهای مهم به‌صورت دستی
            important_files_extra = [
        "group_data.json",
        "fortunes.json",
        "jokes.json",
        "fortunes_media",          # پوشه مدیا کامل
        "group_control/aliases.json",
        "aliases.json",
        "custom_commands.json",    # دستورهای ذخیره شده
        "custom_commands_backup.json",  # حتماً اضافه شود
            ]
            for imp in important_files_extra:
                if os.path.exists(imp):
                    if os.path.isdir(imp):
                        # اضافه کردن کل محتویات پوشه
                        for root, _, files in os.walk(imp):
                            for file in files:
                                full_path = os.path.join(root, file)
                                arcname = os.path.relpath(full_path, ".")
                                zipf.write(full_path, arcname=arcname)
                    else:
                        zipf.write(imp)
                    print(f"📦 اضافه شد به بک‌آپ: {imp}")

            # 🔍 اسکن کل پروژه برای سایر فایل‌های مهم
            for root, _, files in os.walk("."):
                for file in files:
                    full_path = os.path.join(root, file)
                    if _should_include_in_backup(full_path):
                        arcname = os.path.relpath(full_path, ".")
                        zipf.write(full_path, arcname=arcname)

        # 💾 ارسال فایل بک‌آپ
        size_mb = os.path.getsize(filename) / (1024 * 1024)
        caption = (
            f"🧠 <b>بک‌آپ جدید ساخته شد!</b>\n"
            f"📅 تاریخ: <code>{now}</code>\n"
            f"💾 حجم: <code>{size_mb:.2f} MB</code>\n"
            f"☁️ نوع: {reason}"
        )

        with open(filename, "rb") as f:
            await bot.send_document(chat_id=ADMIN_ID, document=f, caption=caption, parse_mode="HTML")

        print(f"✅ بک‌آپ ارسال شد ({size_mb:.2f} MB)")

    except Exception as e:
        print(f"[CLOUD BACKUP ERROR] {e}")
        try:
            await bot.send_message(chat_id=ADMIN_ID, text=f"⚠️ خطا در Cloud Backup:\n{e}")
        except:
            pass
    finally:
        if os.path.exists(filename):
            os.remove(filename)

# ======================= 💬 دستور /cloudsync برای سودو =======================
async def cloudsync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اجرای دستی بک‌آپ ابری"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")
    await cloudsync_internal(context.bot, "Manual Cloud Backup")

# ======================= 💾 بک‌آپ و بازیابی ZIP در چت =======================
async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بک‌آپ دستی و ارسال در چت"""
    await cloudsync_internal(context.bot, "Manual Backup")
    await update.message.reply_text("✅ بک‌آپ کامل گرفته شد و ارسال شد!")

async def restore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت فایل ZIP برای بازیابی"""
    await update.message.reply_text("📂 فایل ZIP بک‌آپ را بفرست تا بازیابی شود.")
    context.user_data["await_restore"] = True

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش فایل ZIP و بازیابی ایمن"""
    if not context.user_data.get("await_restore"):
        return

    doc = update.message.document
    if not doc or not doc.file_name.lower().endswith(".zip"):
        return await update.message.reply_text("❗ لطفاً فقط فایل ZIP معتبر بفرست.")

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

        # 🧩 فایل‌های مهم برای بازیابی
        important_files = [
            "group_data.json",
            "jokes.json",
            "fortunes.json",
            "fortunes_media",
            "aliases.json",
            "group_control/aliases.json"
        ]

        moved_any = False
        for fname in important_files:
            src = os.path.join(restore_dir, fname)
            dest = fname
            dest_dir = os.path.dirname(dest)

            if os.path.exists(src):
                if os.path.isdir(src):
                    # کپی کل محتویات پوشه مدیا
                    if os.path.exists(dest):
                        shutil.rmtree(dest)
                    shutil.copytree(src, dest)
                else:
                    if dest_dir and not os.path.exists(dest_dir):
                        os.makedirs(dest_dir, exist_ok=True)
                    shutil.move(src, dest)
                moved_any = True
                print(f"♻️ بازیابی فایل: {fname}")

        
        if moved_any:
            await update.message.reply_text("✅ بازیابی کامل انجام شد!")
        else:
            await update.message.reply_text("ℹ️ فایلی برای جایگزینی پیدا نشد.")

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در بازیابی:\n{e}")

    finally:
        if os.path.exists(restore_zip):
            os.remove(restore_zip)
        if os.path.exists(restore_dir):
            shutil.rmtree(restore_dir)
        context.user_data["await_restore"] = False
