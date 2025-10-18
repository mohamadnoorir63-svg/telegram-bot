import os
import asyncio
from telegram import Bot, InputFile

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7089376754"))
BRAIN_PATH = "/app/khengol_brain.zip"

async def main():
    bot = Bot(token=TOKEN)
    if os.path.exists(BRAIN_PATH):
        await bot.send_document(
            chat_id=ADMIN_ID,
            document=InputFile(BRAIN_PATH),
            caption="🧠 مغز خِنگول آماده‌ست! فایل ZIP با موفقیت ساخته شد ❤️",
        )
        print("✅ فایل برای سودو ارسال شد.")
    else:
        print("⚠️ فایل پیدا نشد:", BRAIN_PATH)

if __name__ == "__main__":
    asyncio.run(main())
