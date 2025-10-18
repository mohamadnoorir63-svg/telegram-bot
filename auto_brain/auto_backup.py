import os
import time
import zipfile
import telebot
from datetime import datetime, timedelta
import threading

# 📦 خواندن از تنظیمات هاست (Heroku Config Vars)
ADMIN_ID = int(os.getenv("ADMIN_ID", "7089376754"))
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN)

BACKUP_FOLDER = "backups"
SOURCE_FILE = "group_data.json"  # 👈 اگه حافظه‌ت فایل دیگه‌ایه، اسمشو اینجا بزن
KEEP_DAYS = 7  # ⏳ تعداد روزهایی که بک‌آپ نگه‌داشته میشه

def cleanup_old_backups():
    """حذف بک‌آپ‌های قدیمی‌تر از ۷ روز"""
    if not os.path.exists(BACKUP_FOLDER):
        return

    now = datetime.now()
    removed = 0

    for file in os.listdir(BACKUP_FOLDER):
        path = os.path.join(BACKUP_FOLDER, file)
        if os.path.isfile(path):
            mtime = datetime.fromtimestamp(os.path.getmtime(path))
            if now - mtime > timedelta(days=KEEP_DAYS):
                os.remove(path)
                removed += 1
                print(f"🗑️ حذف بک‌آپ قدیمی: {file}")

    if removed > 0:
        print(f"♻️ {removed} فایل قدیمی پاک شد تا فضا آزاد بشه.")


def create_backup():
    """ایجاد و ارسال فایل بک‌آپ ZIP با زمان و حجم"""
    if not os.path.exists(BACKUP_FOLDER):
        os.makedirs(BACKUP_FOLDER)

    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_name = f"{BACKUP_FOLDER}/backup_{now}.zip"

    # ساخت فایل ZIP از حافظه اصلی
    with zipfile.ZipFile(backup_name, "w", zipfile.ZIP_DEFLATED) as zipf:
        if os.path.exists(SOURCE_FILE):
            zipf.write(SOURCE_FILE)
        else:
            print(f"⚠️ فایل {SOURCE_FILE} پیدا نشد، بک‌آپ خالی ساخته شد.")

    # محاسبه حجم فایل
    size_bytes = os.path.getsize(backup_name)
    size_mb = size_bytes / (1024 * 1024)
    size_text = f"{size_mb:.2f} MB"

    # ارسال به ادمین
    try:
        caption = (
            f"🧠 <b>بک‌آپ جدید ساخته شد!</b>\n\n"
            f"📅 تاریخ: <code>{now}</code>\n"
            f"💾 حجم فایل: <code>{size_text}</code>\n"
            f"✅ فایل برای ذخیره ارسال شد."
        )
        with open(backup_name, "rb") as f:
            bot.send_document(ADMIN_ID, f, caption=caption, parse_mode="HTML")

        print(f"✅ بک‌آپ ساخته و ارسال شد ({size_text}) — {backup_name}")

        # بعد از ساخت بک‌آپ، بک‌آپ‌های قدیمی پاک میشن
        cleanup_old_backups()

    except Exception as e:
        print("❌ خطا در ارسال بک‌آپ:", e)


def auto_backup_loop():
    """حلقه‌ی خودکار برای بک‌آپ هر ۶ ساعت"""
    # اجرای فوری در شروع
    create_backup()

    # تکرار هر ۶ ساعت
    while True:
        time.sleep(6 * 60 * 60)
        create_backup()


# اجرای خودکار در نخ جداگانه
threading.Thread(target=auto_backup_loop, daemon=True).start()
