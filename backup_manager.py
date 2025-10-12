import os
import zipfile
from datetime import datetime

BACKUP_FILES = [
    "memory.json",
    "group_data.json",
    "stickers.json",
    "jokes.json",
    "fortunes.json"
]

# ======================= 📦 ایجاد بک‌آپ ZIP =======================

def create_backup(filename=None):
    """ساخت فایل ZIP از داده‌های اصلی"""
    if not filename:
        filename = f"backup_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.zip"

    with zipfile.ZipFile(filename, "w") as zipf:
        for file in BACKUP_FILES:
            if os.path.exists(file):
                zipf.write(file)

    return filename

# ======================= 📤 بازیابی از بک‌آپ =======================

def restore_backup(zip_path):
    """بازیابی کامل از فایل ZIP بک‌آپ"""
    if not os.path.exists(zip_path):
        raise FileNotFoundError("❌ فایل بک‌آپ پیدا نشد!")

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(".")

    return True

# ======================= 🧹 حذف بک‌آپ موقت =======================

def cleanup_backup(filename):
    """حذف فایل ZIP موقت پس از ارسال"""
    try:
        if os.path.exists(filename):
            os.remove(filename)
    except Exception as e:
        print(f"[CLEANUP ERROR] {e}")

# ======================= ☁️ بک‌آپ ابری =======================

async def send_backup_to_admin(bot, admin_id, reason="Manual Backup"):
    """ارسال بک‌آپ ZIP به سودو"""
    filename = create_backup()
    try:
        await bot.send_document(chat_id=admin_id, document=open(filename, "rb"), filename=filename)
        await bot.send_message(chat_id=admin_id, text=f"☁️ {reason} انجام شد ✅")
        print(f"[CLOUD BACKUP] {reason} sent ✅")
    except Exception as e:
        print(f"[CLOUD BACKUP ERROR] {e}")
    finally:
        cleanup_backup(filename)
