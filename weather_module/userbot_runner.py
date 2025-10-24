from pyrogram import Client, filters
import os, asyncio

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION = os.getenv("SESSION_STRING", "")

userbot = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)

@userbot.on_message(filters.text & ~filters.edited)
async def handle_user_message(client, message):
    text = message.text.lower()

    # مثال: جواب ساده یا دریافت لینک آهنگ
    if "آهنگ" in text or "music" in text:
        await message.reply_text("🎶 در حال جستجو برای آهنگ شما ...")

    elif text == "ping":
        await message.reply_text("✅ Userbot Online!")

async def start_userbot():
    print("🚀 Starting userbot...")
    await userbot.start()
    print("✅ Userbot connected.")
    await asyncio.Event().wait()
