import os
import asyncio
import random
from telethon import TelegramClient, events

# ================= ⚙️ خواندن اطلاعات از محیط =================
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
SESSION_STRING = os.environ.get("SESSION_STRING", "")
BOT_USER_ID = int(os.environ.get("BOT_USER_ID", 0))

if not all([API_ID, API_HASH, SESSION_STRING, BOT_USER_ID]):
    raise ValueError("API_ID, API_HASH, SESSION_STRING و BOT_USER_ID باید تعریف شوند!")

# ================= ⚙️ تعریف یوزربات =================
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

async def start_userbot():
    """اجرای یوزربات"""
    await client.start()
    print("✅ Userbot آماده و متصل شد!")

    @client.on(events.NewMessage)
    async def handle_commands(event):
        text = event.raw_text
        sender = await event.get_sender()
        if sender.id != BOT_USER_ID:
            return
        # دستورها را اینجا پردازش کن
        if text.lower() == "tagall":
            await tag_all(event.chat_id)

    async def tag_all(chat_id):
        participants = await client.get_participants(chat_id)
        mentions = [f"[{p.first_name}](tg://user?id={p.id})" for p in participants if not p.bot]
        chunk_size = 20
        for i in range(0, len(mentions), chunk_size):
            await client.send_message(chat_id, "👥 " + " ".join(mentions), parse_mode="md")
            await asyncio.sleep(1)

    await client.run_until_disconnected()
