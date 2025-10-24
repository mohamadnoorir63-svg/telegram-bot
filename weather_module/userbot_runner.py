from pyrogram import Client, filters
import os, asyncio

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION = os.getenv("SESSION_STRING", "")

userbot = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)
@userbot.on_message(filters.text & (filters.private | filters.group | filters.me))
async def handle_message(client, message):
    text = message.text.strip()
    print(f"📩 Userbot received: {text}")

    if text.lower() == "ping":
        return await message.reply_text("✅ Userbot Online!")

    if text.startswith("آهنگ "):
        query = text.replace("آهنگ", "").strip()
        if not query:
            return await message.reply_text("❗ لطفاً بعد از 'آهنگ' نام آهنگ را بنویس.")

        m = await message.reply_text("🎧 در حال جستجو و دانلود آهنگ...")
        ...
async def start_userbot():
    print("🚀 Starting userbot...")
    await userbot.start()
    me = await userbot.get_me()
    print(f"✅ Userbot logged in as {me.first_name} ({me.id})")
    await asyncio.Event().wait()
