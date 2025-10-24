from pyrogram import Client, filters
import os, asyncio

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION = os.getenv("SESSION_STRING", "")

userbot = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)

@userbot.on_message(filters.text & ~filters.edited)
async def handle_user_message(client, message):
    text = message.text.lower()

    # لاگ ساده برای نمایش پیام‌های دریافتی
    print(f"📩 Userbot received: {text} | from {message.from_user.id}")

    if text == "ping":
        await message.reply_text("✅ Userbot Online!")

    elif "آهنگ" in text:
        await message.reply_text("🎶 در حال جستجو برای آهنگ شما ...")

    elif text == "id":
        await message.reply_text(f"🆔 Your ID: `{message.from_user.id}`")

async def start_userbot():
    """اجرای یوزربات و چاپ مشخصات ورود"""
    print("🚀 Starting userbot...")
    await userbot.start()
    me = await userbot.get_me()
    print(f"✅ Userbot logged in as {me.first_name} ({me.id})")
    await asyncio.Event().wait()
