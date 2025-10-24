from pyrogram import Client, filters
import os, asyncio

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION = os.getenv("SESSION_STRING", "")

# 📱 ساخت کلاینت یوزربات
userbot = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)

# 🎧 هندل پیام‌های دریافتی
@userbot.on_message(filters.text)
async def handle_user_message(client, message):
    text = message.text.lower()

    if "آهنگ" in text:
        await message.reply_text("🎶 در حال جستجو برای آهنگ شما ...")

    elif text == "ping":
        await message.reply_text("✅ Userbot Online!")

# 🚀 تابع استارت برای اجرای یوزربات در کنار بات اصلی
async def start_userbot():
    print("🚀 Starting userbot...")
    await userbot.start()
    print("✅ Userbot connected.")
    await asyncio.Event().wait()
