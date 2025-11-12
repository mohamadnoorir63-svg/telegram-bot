import os
import asyncio
import random
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ================= ⚙️ تنظیمات یوزربات =================
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION_STRING = os.getenv("SESSION_STRING", "")
BOT_USER_ID = int(os.getenv("BOT_USER_ID", "0"))

if not all([API_ID, API_HASH, SESSION_STRING, BOT_USER_ID]):
    raise ValueError("API_ID, API_HASH, SESSION_STRING و BOT_USER_ID باید تعریف شوند!")

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# ================= 📝 توابع تگ =================
async def tag_all(chat_id):
    try:
        all_members = await client.get_participants(chat_id)
        mentions = [f"[{m.first_name}](tg://user?id={m.id})" for m in all_members if not m.bot]
        if not mentions:
            await client.send_message(chat_id, "ℹ️ هیچ کاربر مناسبی برای تگ پیدا نشد.")
            return
        # ارسال در پیام‌های ۲۰ نفره
        for i in range(0, len(mentions), 20):
            chunk = mentions[i:i+20]
            await client.send_message(chat_id, "👥 " + " ".join(chunk), parse_mode="md")
            await asyncio.sleep(1)
    except Exception as e:
        await client.send_message(chat_id, f"⚠️ خطا در tag_all: {e}")

async def tag_admins(chat_id):
    try:
        admins = await client.get_participants(chat_id, filter=lambda m: m.admin_rights or m.creator)
        mentions = [f"[{a.first_name}](tg://user?id={a.id})" for a in admins if not a.bot]
        if not mentions:
            await client.send_message(chat_id, "ℹ️ هیچ مدیر فعالی در گروه وجود ندارد.")
            return
        for i in range(0, len(mentions), 20):
            chunk = mentions[i:i+20]
            await client.send_message(chat_id, "👑 " + " ".join(chunk), parse_mode="md")
            await asyncio.sleep(1)
    except Exception as e:
        await client.send_message(chat_id, f"⚠️ خطا در tag_admins: {e}")

async def tag_random(chat_id, count=5):
    try:
        all_members = await client.get_participants(chat_id)
        members = [m for m in all_members if not m.bot]
        if not members:
            await client.send_message(chat_id, "ℹ️ هیچ کاربر مناسبی برای تگ تصادفی وجود ندارد.")
            return
        sample = random.sample(members, min(count, len(members)))
        mentions = [f"[{m.first_name}](tg://user?id={m.id})" for m in sample]
        await client.send_message(chat_id, "🎲 تگ تصادفی:\n" + " ".join(mentions), parse_mode="md")
    except Exception as e:
        await client.send_message(chat_id, f"⚠️ خطا در tag_random: {e}")

# ================= ⚡ دریافت دستورات از بوت رسمی =================
@client.on(events.NewMessage)
async def handle_commands(event):
    text = event.raw_text
    sender = await event.get_sender()

    # فقط پیام‌های بوت رسمی را پردازش کن
    if sender.id != BOT_USER_ID:
        return

    parts = text.split("|")
    if len(parts) < 2:
        return

    action = parts[0].strip().lower()
    chat_id = int(parts[1])

    if action == "tagall":
        await tag_all(chat_id)
    elif action == "tagadmins":
        await tag_admins(chat_id)
    elif action.startswith("tagrandom"):
        count = 5
        if len(parts) == 3 and parts[2].isdigit():
            count = int(parts[2])
        await tag_random(chat_id, count)

# ================= 🚀 اجرا =================
async def start_userbot():
    await client.start()
    print("✅ Userbot ready and listening to bot commands...")
    await client.run_until_disconnected()
