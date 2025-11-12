import os
import asyncio
import random
from telethon import TelegramClient, events, sessions
from telethon.tl.types import Channel

# ================= ⚙️ اطلاعات یوزربات =================
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")

if not all([API_ID, API_HASH, SESSION_STRING]):
    raise ValueError("API_ID, API_HASH و SESSION_STRING باید تعریف شوند!")

client = TelegramClient(sessions.StringSession(SESSION_STRING), API_ID, API_HASH)

# ================= 🧩 توابع تگ =================
async def tag_all(chat_id):
    members = await client.get_participants(chat_id)
    mentions = [f"[{m.first_name}](tg://user?id={m.id})" for m in members if not m.bot]
    chunk_size = 20
    for i in range(0, len(mentions), chunk_size):
        await client.send_message(chat_id, "👥 " + " ".join(mentions), parse_mode="md")
        await asyncio.sleep(1)

async def tag_random(chat_id, count=5):
    members = await client.get_participants(chat_id)
    non_bots = [m for m in members if not m.bot]
    sample = random.sample(non_bots, min(count, len(non_bots)))
    mentions = [f"[{m.first_name}](tg://user?id={m.id})" for m in sample]
    await client.send_message(chat_id, "🎲 تگ تصادفی:\n" + " ".join(mentions), parse_mode="md")

# ================= ⚡ دریافت فرمان فارسی از گروه =================
@client.on(events.NewMessage)
async def handle_group_commands(event):
    chat = await event.get_chat()
    sender = await event.get_sender()
    text = (event.raw_text or "").strip()

    # فقط گروه‌ها
    if not isinstance(chat, Channel):
        return

    # ------------------ تگ همه ------------------
    if text == "تگ همه":
        await tag_all(chat.id)
    
    # ------------------ تگ تصادفی ------------------
    elif text.startswith("تگ تصادفی"):
        parts = text.split()
        count = 5
        if len(parts) > 1 and parts[1].isdigit():
            count = int(parts[1])
        await tag_random(chat.id, count)

# ================= 🚀 استارت یوزربات =================
async def start_userbot():
    await client.start()
    print("✅ Userbot آماده و گوش به فرمان است...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(start_userbot())
