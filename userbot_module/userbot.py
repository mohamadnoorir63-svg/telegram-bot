import os
import asyncio
import random
from telethon import TelegramClient, events

API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")
BOT_USER_ID = int(os.environ.get("BOT_USER_ID", 0))

if not API_ID or not API_HASH or not SESSION_STRING or not BOT_USER_ID:
    raise ValueError("API_ID, API_HASH, SESSION_STRING و BOT_USER_ID باید تعریف شوند!")

client = TelegramClient.from_session_string(SESSION_STRING, API_ID, API_HASH)

# ======= توابع تگ =======
async def tag_all(chat_id):
    try:
        all_members = await client.get_participants(chat_id)
        mentions = [f"[{m.first_name}](tg://user?id={m.id})" for m in all_members if not m.bot]
        chunk_size = 20
        for i in range(0, len(mentions), chunk_size):
            await client.send_message(chat_id, "👥 " + " ".join(mentions[i:i + chunk_size]), parse_mode="md")
            await asyncio.sleep(1)
    except Exception as e:
        await client.send_message(chat_id, f"⚠️ خطا در tag_all: {e}")

# ======= دریافت دستورات بوت رسمی =======
@client.on(events.NewMessage)
async def handle_commands(event):
    sender = await event.get_sender()
    if sender.id != BOT_USER_ID:
        return
    text = event.raw_text
    parts = text.split("|")
    if len(parts) < 2:
        return
    action = parts[0].strip().lower()
    chat_id = int(parts[1])
    if action == "tagall":
        await tag_all(chat_id)

# ======= شروع یوزربات =======
async def start_userbot():
    await client.start()
    print("✅ Userbot started")
    await client.run_until_disconnected()
