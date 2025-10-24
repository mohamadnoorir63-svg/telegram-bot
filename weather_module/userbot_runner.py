from pyrogram import Client, filters
import os

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION = os.getenv("SESSION_STRING", "")

userbot = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)

@userbot.on_message(filters.text)
async def handle_message(client, message):
    text = message.text.strip()
    print(f"📩 Userbot دریافت کرد: {text}")

    if text.lower() == "ping":
        await message.reply_text("✅ Userbot فعال است!")


def start_userbot():
    """شروع Userbot در subprocess جدا بدون asyncio تداخل"""
    import threading
    import asyncio

    def _worker():
        asyncio.run(run_userbot())

    threading.Thread(target=_worker, daemon=True).start()


async def run_userbot():
    """اجرای کامل Userbot"""
    try:
        print("🚀 Starting userbot...")
        await userbot.start()
        me = await userbot.get_me()
        print(f"✅ Userbot وارد شد: {me.first_name} ({me.id})")
        await userbot.idle()
    except Exception as e:
        print(f"⚠️ خطا در userbot: {e}")
