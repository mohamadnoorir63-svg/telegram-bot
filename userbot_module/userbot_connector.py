import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import random

# ================= ⚙️ تنظیمات یوزربات =================
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")
BOT_USER_ID = int(os.environ.get("BOT_USER_ID", 0))  # آیدی ربات اصلی

if not all([API_ID, API_HASH, SESSION_STRING, BOT_USER_ID]):
    raise ValueError("API_ID, API_HASH, SESSION_STRING و BOT_USER_ID باید تعریف شوند!")

userbot_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# ================= 📝 توابع تگ =================
async def tag_all(chat_id):
    try:
        all_members = await userbot_client.get_participants(chat_id)
        mentions = [f"[{m.first_name}](tg://user?id={m.id})" for m in all_members if not m.bot]
        if not mentions:
            await userbot_client.send_message(chat_id, "ℹ️ هیچ کاربر مناسبی برای تگ پیدا نشد.")
            return

        # دسته‌بندی برای پیام‌های ۲۰ نفره
        for i in range(0, len(mentions), 20):
            chunk = mentions[i:i+20]
            await userbot_client.send_message(chat_id, "👥 " + " ".join(chunk), parse_mode="md")
            await asyncio.sleep(1)

    except Exception as e:
        await userbot_client.send_message(chat_id, f"⚠️ خطا در tag_all: {e}")

async def tag_random(chat_id, count=5):
    try:
        all_members = await userbot_client.get_participants(chat_id)
        members = [m for m in all_members if not m.bot]
        if not members:
            await userbot_client.send_message(chat_id, "ℹ️ هیچ کاربر مناسبی برای تگ تصادفی وجود ندارد.")
            return
        sample = random.sample(members, min(count, len(members)))
        mentions = [f"[{m.first_name}](tg://user?id={m.id})" for m in sample]
        await userbot_client.send_message(chat_id, "🎲 تگ تصادفی:\n" + " ".join(mentions), parse_mode="md")
    except Exception as e:
        await userbot_client.send_message(chat_id, f"⚠️ خطا در tag_random: {e}")

# ================= ⚡ دریافت فرمان از ربات اصلی =================
@userbot_client.on(events.NewMessage)
async def handle_commands(event):
    sender = await event.get_sender()
    text = event.raw_text
    if sender.id != BOT_USER_ID:
        return

    parts = text.split("|")
    if len(parts) < 2:
        return

    action = parts[0].strip().lower()
    chat_id = int(parts[1])
    count = int(parts[2]) if len(parts) == 3 and parts[2].isdigit() else 5

    if action == "tagall":
        await tag_all(chat_id)
    elif action.startswith("tagrandom"):
        await tag_random(chat_id, count)

# ================= 🚀 اجرا =================
async def start_userbot():
    await userbot_client.start()
    print("✅ Userbot ready and listening to bot commands...")
    await userbot_client.run_until_disconnected()
