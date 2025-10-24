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


def start_userbot():
    """اجرا در ترد جدا بدون تداخل با event loop اصلی"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_userbot())


async def run_userbot():
    try:
        print("🚀 Starting userbot...")
        await userbot.start()
        me = await userbot.get_me()
        print(f"✅ Userbot logged in as {me.first_name} ({me.id})")
        await userbot.idle()
    except Exception as e:
        print(f"⚠️ خطا در اجرای userbot: {e}")
