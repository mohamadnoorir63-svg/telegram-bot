from pyrogram import Client, filters
import os, asyncio

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION = os.getenv("SESSION_STRING", "")

userbot = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)


@userbot.on_message(filters.text)
async def handle_message(client, message):
    text = message.text.strip()
    print(f"📩 Userbot received: {text}")

    if text.lower() == "ping":
        await message.reply_text("✅ Userbot Online!")


async def start_userbot():
    """اجرای userbot در همون event loop بدون ایجاد loop جدید"""
    try:
        print("🚀 Starting userbot...")

        # اجرای userbot در پس‌زمینه تا تداخل با event loop اصلی نداشته باشه
        loop = asyncio.get_running_loop()
        loop.create_task(_run_userbot())

    except Exception as e:
        print(f"⚠️ خطا در راه‌اندازی userbot: {e}")


async def _run_userbot():
    """اجرای واقعی یوزربات (داخل تسک جداگانه)"""
    await userbot.start()
    me = await userbot.get_me()
    print(f"✅ Userbot logged in as {me.first_name} ({me.id})")

    await userbot.idle()  # تا همیشه فعال بمونه
