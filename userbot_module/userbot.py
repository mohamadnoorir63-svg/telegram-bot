# ======= بالای فایل، بعد از import ها =======
import asyncio
from telethon import TelegramClient, events
import os
import random

# ================= ⚙️ تنظیمات یوزربات =================
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")
BOT_USER_ID = int(os.environ.get("BOT_USER_ID", 0))  # آیدی بوت رسمی

if not API_ID or not API_HASH or not SESSION_STRING or not BOT_USER_ID:
    raise ValueError("API_ID, API_HASH, SESSION_STRING و BOT_USER_ID باید تعریف شوند!")

userbot_client = TelegramClient.from_session_string(SESSION_STRING, API_ID, API_HASH)

# ================= 📝 توابع تگ =================
async def tag_all(chat_id):
    try:
        all_members = await userbot_client.get_participants(chat_id)
        mentions = [f"[{m.first_name}](tg://user?id={m.id})" for m in all_members if not m.bot]
        if not mentions:
            await userbot_client.send_message(chat_id, "ℹ️ هیچ کاربر مناسبی برای تگ پیدا نشد.")
            return
        chunk_size = 20
        for i in range(0, len(mentions), chunk_size):
            await userbot_client.send_message(chat_id, "👥 " + " ".join(mentions[i:i + chunk_size]), parse_mode="md")
            await asyncio.sleep(1)
    except Exception as e:
        await userbot_client.send_message(chat_id, f"⚠️ خطا در tag_all: {e}")

# مشابه توابع tag_admins و tag_random را هم اضافه کن...

# ================= ⚡ دریافت دستورات از بوت رسمی =================
@userbot_client.on(events.NewMessage)
async def handle_commands(event):
    text = event.raw_text
    sender = await event.get_sender()
    if sender.id != BOT_USER_ID:
        return

    parts = text.split("|")
    if len(parts) < 2:
        return

    action = parts[0].strip().lower()
    chat_id = int(parts[1])

    if action == "tagall":
        await tag_all(chat_id)
    # elif action == "tagadmins":
    #     await tag_admins(chat_id)
    # elif action.startswith("tagrandom"):
    #     await tag_random(chat_id, count)

# ================= 🔥 تابع شروع یوزربات =================
async def start_userbot():
    await userbot_client.start()
    print("✅ Userbot started and listening...")
    await userbot_client.run_until_disconnected()
