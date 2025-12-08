# ======================= ☁️ Backup & Restore System — Final Version =======================

import os
import zipfile
import shutil
import asyncio
import json
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

BACKUP_FOLDER = "backups"
ADMIN_ID = int(os.getenv("ADMIN_ID", "8588347189"))

# ======================= 🧠 توابع پایه =======================

def _should_include_in_backup(path: str) -> bool:
    lowered = path.lower()

    skip_dirs = ["__pycache__", ".git", "venv", "restore_temp", BACKUP_FOLDER]
    if any(s in lowered for s in skip_dirs):
        return False

    if lowered.endswith(".zip") or os.path.basename(lowered).startswith("backup_"):
        return False

    important_files = [
        "data/groups.json",
        "data/users.json",
        "data/custom_commands.json",
        "custom_commands_backup.json",
        "data/youtube_cache.json",
        "data/sound_cache.json",
        "fortunes.json",
        "jokes.json",
        "stickers.json",
        "aliases.json",
        "group_control/aliases.json",
        "fortunes_media",
    ]

    if any(path.endswith(f) or f in path for f in important_files):
        return True

    return lowered.endswith((".json", ".jpg", ".jpeg", ".png", ".webp", ".mp3", ".ogg"))


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

        with zipfile.ZipFile(filename, "w", zipfile.ZIP_DEFLATED) as zipf:

            important_files_force = [
                "data/groups.json",
                "data/users.json",
                "data/custom_commands.json",
                "custom_commands_backup.json",
                "data/youtube_cache.json",
                "data/sound_cache.json",
                "jokes.json",
                "fortunes.json",
                "aliases.json",
                "group_control/aliases.json",
                "fortunes_media",
            ]

            for f in important_files_force:
                if os.path.exists(f):
                    if os.path.isdir(f):
                        for root, _, files in os.walk(f):
                            for file in files:
                                full = os.path.join(root, file)
                                arc = os.path.relpath(full, ".")
                                zipf.write(full, arc)
                    else:
                        zipf.write(f, f)

            for root, _, files in os.walk("."):
                for file in files:
                    full = os.path.join(root, file)
                    if _should_include_in_backup(full):
                        arc = os.path.relpath(full, ".")
                        zipf.write(full, arc)

        size = os.path.getsize(filename) / (1024 * 1024)

        caption = (
            f"🧠 <b>بک‌آپ جدید ساخته شد!</b>\n"
            f"📅 تاریخ: <code>{now}</code>\n"
            f"💾 حجم: <code>{size:.2f} MB</code>\n"
            f"☁️ نوع: {reason}"
        )

        with open(filename, "rb") as f:
            await bot.send_document(ADMIN_ID, f, caption=caption, parse_mode="HTML")

    except Exception as e:
        await bot.send_message(ADMIN_ID, f"⚠️ خطا در بک‌آپ:\n{e}")

    finally:
        if os.path.exists(filename):
            os.remove(filename)


# ======================= 💬 دستور /cloudsync =======================

async def cloudsync(update, context):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی!")

    await cloudsync_internal(context.bot, "Manual Cloud Backup")


# ======================= 💾 بک‌آپ دستی =======================

async def backup(update, context):
    await cloudsync_internal(context.bot, "Manual Backup")
    await update.message.reply_text("✅ بک‌آپ کامل گرفته شد!")


# ======================= 📂 بازیابی =======================

async def restore(update, context):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی!")

    context.user_data["await_restore"] = True
    await update.message.reply_text("📂 لطفاً فایل ZIP بک‌آپ را ارسال کنید.")


# پیدا کردن فایل داخل ZIP حتی اگر مسیر متفاوت باشد
def find_file(root, target):
    found = []
    for r, dirs, files in os.walk(root):
        for d in dirs:
            full = os.path.join(r, d)
            if full.replace("\\", "/").endswith(target):
                found.append(full)
        for f in files:
            full = os.path.join(r, f)
            if full.replace("\\", "/").endswith(target):
                found.append(full)
    return found


async def handle_document(update, context):
    if not context.user_data.get("await_restore"):
        return

    doc = update.message.document
    if not doc or not doc.file_name.lower().endswith(".zip"):
        return await update.message.reply_text("❗ فقط ZIP معتبر ارسال کن.")

    restore_zip = "restore.zip"
    restore_dir = "restore_temp"

    try:
        tg = await doc.get_file()
        await tg.download_to_drive(restore_zip)

        if os.path.exists(restore_dir):
            shutil.rmtree(restore_dir)
        os.makedirs(restore_dir)

        with zipfile.ZipFile(restore_zip, "r") as z:
            z.extractall(restore_dir)

        important = [
            "data/groups.json",
            "data/users.json",
            "data/custom_commands.json",
            "custom_commands_backup.json",
            "data/youtube_cache.json",
            "data/sound_cache.json",
            "jokes.json",
            "fortunes.json",
            "aliases.json",
            "group_control/aliases.json",
            "fortunes_media",
        ]

        restored = False

        for f in important:
            matches = find_file(restore_dir, f)
            if not matches:
                continue

            src = matches[0]
            dst = f

            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)

            restored = True

        if restored:
            await update.message.reply_text("✅ بازیابی کامل انجام شد!")
        else:
            await update.message.reply_text("ℹ️ هیچ فایل مهمی برای بازیابی پیدا نشد.")

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در بازیابی:\n{e}")

    finally:
        if os.path.exists(restore_zip):
            os.remove(restore_zip)
        if os.path.exists(restore_dir):
            shutil.rmtree(restore_dir)
        context.user_data["await_restore"] = False
