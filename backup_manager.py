import os
import zipfile
from datetime import datetime

async def create_backup(filename=None):
    """ساخت بک‌آپ ZIP از تمام فایل‌های اصلی"""
    if not filename:
        filename = f"backup_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.zip"

    with zipfile.ZipFile(filename, "w") as zipf:
        for root, _, files in os.walk("."):
            for file in files:
                if file.endswith((".json", ".jpg", ".png", ".webp", ".mp3", ".ogg")):
                    path = os.path.join(root, file)
                    zipf.write(path)
    return filename

async def send_backup(bot, admin_id, reason="Manual Backup"):
    """ارسال بک‌آپ ZIP به مدیر"""
    try:
        filename = await create_backup()
        await bot.send_document(chat_id=admin_id, document=open(filename, "rb"), filename=filename)
        await bot.send_message(chat_id=admin_id, text=f"☁️ بک‌آپ {reason} ارسال شد ✅")
        os.remove(filename)
    except Exception as e:
        print(f"[BACKUP ERROR] {e}")

async def auto_backup_loop(bot, admin_id):
    """بک‌آپ خودکار هر ۱۲ ساعت"""
    import asyncio
    while True:
        await asyncio.sleep(43200)
        await send_backup(bot, admin_id, "Auto Backup")
