# userbot.py
from telethon import TelegramClient
from telethon.sessions import StringSession
import os, asyncio

message_queue = asyncio.Queue()  # ✅ صف داخلی اشتراک پیام‌ها بین ربات و یوزربات

async def start_userbot():
    api_id = int(os.getenv("API_ID", "0"))
    api_hash = os.getenv("API_HASH", "")
    session_string = os.getenv("SESSION_STRING", "")

    if not api_id or not api_hash:
        print("🚫 API_ID یا API_HASH تنظیم نشده — userbot غیرفعاله.")
        return

    client = TelegramClient(StringSession(session_string), api_id, api_hash)
    await client.start()
    me = await client.get_me()
    print(f"✅ Userbot فعال شد: {me.first_name} [ID: {me.id}]")

    async def userbot_worker():
        """📨 بررسی پیام‌های ارسالی از ربات اصلی"""
        while True:
            msg = await message_queue.get()
            chat_id, text = msg.get("chat_id"), msg.get("text")
            print(f"📥 پیام از bot اصلی: {text}")
            # مثلا اگر پیام شامل 'سلام' بود، userbot جواب بده
            if "سلام" in text:
                await client.send_message(chat_id, "سلام از سمت یوزربات 😎")
            message_queue.task_done()

    asyncio.create_task(userbot_worker())
    await client.run_until_disconnected()
