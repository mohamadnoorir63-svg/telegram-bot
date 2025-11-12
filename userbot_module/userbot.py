import asyncio
import random
from telethon import TelegramClient, events, sessions

# ================= ⚙️ اطلاعات یوزربات =================
API_ID = int(os.environ.get("API_ID"))           # از my.telegram.org
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")
BOT_USER_ID = int(os.environ.get("BOT_USER_ID"))  # آیدی ربات اصلی که فرمان می‌دهد

if not all([API_ID, API_HASH, SESSION_STRING, BOT_USER_ID]):
    raise ValueError("API_ID, API_HASH, SESSION_STRING و BOT_USER_ID باید تعریف شوند!")

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

# ================= ⚡ دریافت فرمان از ربات اصلی =================
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
    elif action.startswith("tagrandom"):
        count = 5
        if len(parts) == 3 and parts[2].isdigit():
            count = int(parts[2])
        await tag_random(chat_id, count)

# ================= 🚀 استارت یوزربات =================
async def start_userbot():
    await client.start()
    print("✅ Userbot ready and listening to bot commands...")
    await client.run_until_disconnected()
