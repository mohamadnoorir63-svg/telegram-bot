import os
import zipfile
import shutil
import datetime
import asyncio

# ======================= ⚙️ تنظیمات اصلی =======================
BACKUP_INTERVAL = 21600  # ⏰ هر ۶ ساعت
IMPORTANT_FILES = ["memory.json", "group_data.json", "jokes.json", "fortunes.json"]

# ======================= 📦 ساخت بک‌آپ ZIP =======================
async def create_backup(filename=None):
    """ساخت بک‌آپ ZIP از تمام فایل‌های اصلی ربات"""
    if not filename:
        filename = f"backup_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')}.zip"

    with zipfile.ZipFile(filename, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk("."):
            for file in files:
                if file.endswith((".json", ".jpg", ".png", ".webp", ".mp3", ".ogg")):
                    full_path = os.path.join(root, file)
                    arcname = os.path.relpath(full_path, ".")
                    zipf.write(full_path, arcname)
    return filename


# ======================= ☁️ ارسال بک‌آپ =======================
async def send_backup(bot, admin_id, reason="Manual Backup"):
    """ارسال فایل بک‌آپ به مدیر اصلی"""
    try:
        filename = await create_backup()
        with open(filename, "rb") as f:
            await bot.send_document(chat_id=admin_id, document=f, filename=filename)
        await bot.send_message(chat_id=admin_id, text=f"☁️ بک‌آپ {reason} ارسال شد ✅")
    except Exception as e:
        print(f"[BACKUP ERROR] {e}")
        await bot.send_message(chat_id=admin_id, text=f"⚠️ خطا در بک‌آپ:\n{e}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)


# ======================= 🔁 بک‌آپ خودکار =======================
async def auto_backup_loop(bot, admin_id):
    """بک‌آپ خودکار هر ۶ ساعت برای ادمین اصلی"""
    while True:
        await asyncio.sleep(BACKUP_INTERVAL)
        await send_backup(bot, admin_id, "Auto Backup")


# ======================= 🔂 بازیابی فایل‌ها =======================
async def restore(update, context):
    """دستور کاربر برای شروع بازیابی"""
    await update.message.reply_text("📦 لطفاً فایل ZIP بک‌آپ را ارسال کن تا بازیابی شود.")
    context.user_data["await_restore"] = True


async def handle_document(update, context):
    """پردازش فایل ZIP برای بازیابی ایمن"""
    if not context.user_data.get("await_restore"):
        return

    doc = update.message.document
    if not doc or not doc.file_name.lower().endswith(".zip"):
        return await update.message.reply_text("⚠️ لطفاً فقط فایل ZIP بک‌آپ را بفرست.")

    restore_zip = "restore.zip"
    restore_dir = "restore_temp"

    try:
        tg_file = await doc.get_file()
        await tg_file.download_to_drive(restore_zip)

        if os.path.exists(restore_dir):
            shutil.rmtree(restore_dir)
        os.makedirs(restore_dir, exist_ok=True)

        with zipfile.ZipFile(restore_zip, "r") as zip_ref:
            all_files = zip_ref.namelist()
            total = len(all_files)
            done = 0

            msg = await update.message.reply_text("📦 در حال بازیابی...\n0% ▱▱▱▱▱▱▱▱▱▱")
            for file in all_files:
                zip_ref.extract(file, restore_dir)
                done += 1
                percent = int((done / total) * 100)
                blocks = int(percent / 10)
                bar = "▰" * blocks + "▱" * (10 - blocks)
                try:
                    await msg.edit_text(f"📦 در حال بازیابی...\n{percent}% {bar}")
                except:
                    pass
                await asyncio.sleep(0.1)

        # انتقال فایل‌های کلیدی به محل اصلی
        moved_any = False
        for fname in IMPORTANT_FILES:
            src = os.path.join(restore_dir, fname)
            if os.path.exists(src):
                shutil.move(src, fname)
                moved_any = True

        if moved_any:
            await msg.edit_text("✅ بازیابی کامل انجام شد!\nتمام داده‌ها جایگزین شدند.")
        else:
            await msg.edit_text("ℹ️ فایلی برای جایگزینی پیدا نشد. ZIP درست را دادی؟")

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در بازیابی: {e}")

    finally:
        if os.path.exists(restore_zip):
            os.remove(restore_zip)
        if os.path.exists(restore_dir):
            shutil.rmtree(restore_dir)
        context.user_data["await_restore"] = False
