# ================= هماهنگ سازی یوزربات با ربات اصلی =================
import os
import asyncio
import random
from telethon import TelegramClient, events, sessions
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes, MessageHandler, filters
import json
import re

# ---------- یوزربات ----------
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")
BOT_USER_ID = int(os.environ.get("BOT_USER_ID"))

client = TelegramClient(sessions.StringSession(SESSION_STRING), API_ID, API_HASH)

# فایل هشدارها
WARN_FILE = "warnings.json"
SUDO_IDS = [8588347189]

if not os.path.exists(WARN_FILE):
    with open(WARN_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

def _load_json(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def _save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ================= تگ کاربران با یوزربات =================
async def tag_users(chat_id, user_ids=None, random_count=None):
    members = []
    try:
        members = await client.get_participants(chat_id)
    except:
        pass  # اگر یوزربات عضو نبود یا خطایی بود، خالی می‌مونه

    non_bots = [m for m in members if not getattr(m, "bot", False)]
    if random_count:
        non_bots = random.sample(non_bots, min(random_count, len(non_bots)))
    elif user_ids:
        non_bots = [m for m in non_bots if m.id in user_ids]

    mentions = [f"[{m.first_name}](tg://user?id={m.id})" for m in non_bots]

    chunk_size = 20
    for i in range(0, len(mentions), chunk_size):
        await client.send_message(chat_id, "👥 " + " ".join(mentions), parse_mode="md")
        await asyncio.sleep(1)

# ================= ارسال دستورات تنبیهی روی یوزربات =================
async def punish_via_userbot(chat_id, user_id, action="ban", seconds=None):
    try:
        if action == "ban":
            await client.edit_permissions(chat_id, user_id, view_messages=False)
        elif action == "unban":
            await client.edit_permissions(chat_id, user_id, view_messages=True)
        elif action == "mute":
            until = None
            if seconds:
                until = datetime.utcnow() + timedelta(seconds=seconds)
            await client.edit_permissions(chat_id, user_id, send_messages=False, until_date=until)
        elif action == "unmute":
            await client.edit_permissions(chat_id, user_id, send_messages=True)
    except:
        pass

# ================= هماهنگ سازی پاکسازی =================
async def cleanup_messages_via_userbot(chat_id, message_ids=None, last_msg_id=None, n=None):
    """
    حذف پیام‌ها توسط یوزربات حتی اگر در گروه عضو نباشد.
    - message_ids: لیست پیام‌های مشخص
    - last_msg_id: پاکسازی از آخرین پیام تا n
    - n: تعداد پیام برای حذف از آخر
    """
    if message_ids:
        for i in range(0, len(message_ids), 20):
            batch = message_ids[i:i + 20]
            for mid in batch:
                try:
                    await client.delete_messages(chat_id, mid)
                except:
                    continue
            await asyncio.sleep(0.3)
    elif last_msg_id and n:
        for start in range(last_msg_id, max(0, last_msg_id - n), -1):
            try:
                await client.delete_messages(chat_id, start)
            except:
                continue
            await asyncio.sleep(0.2)

# ================= دریافت فرمان از ربات اصلی =================
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

    # ---------- تگ کاربران ----------
    if action == "tagall":
        await tag_users(chat_id)
    elif action.startswith("tagrandom"):
        count = 5
        if len(parts) == 3 and parts[2].isdigit():
            count = int(parts[2])
        await tag_users(chat_id, random_count=count)
    elif action.startswith("taglist"):
        ids = [int(x) for x in parts[2].split(",") if x.isdigit()] if len(parts) > 2 else None
        await tag_users(chat_id, user_ids=ids)

    # ---------- تنبیه ----------
    elif action.startswith("ban"):
        target = parts[2].strip()
        user_id = None
        if target.isdigit():
            user_id = int(target)
        elif target.startswith("@"):
            try:
                user_obj = await client.get_entity(target)
                user_id = user_obj.id
            except:
                pass
        if user_id:
            await punish_via_userbot(chat_id, user_id, action="ban")
    elif action.startswith("unban"):
        target = parts[2].strip()
        user_id = None
        if target.isdigit():
            user_id = int(target)
        elif target.startswith("@"):
            try:
                user_obj = await client.get_entity(target)
                user_id = user_obj.id
            except:
                pass
        if user_id:
            await punish_via_userbot(chat_id, user_id, action="unban")

    # ---------- هماهنگ سازی پاکسازی ----------
    elif action.startswith("cleanup"):
        # parts[2] = تعداد پیام یا لیست پیام_ids جدا شده با ,
        try:
            if len(parts) > 2:
                param = parts[2]
                if "," in param:
                    message_ids = [int(x) for x in param.split(",") if x.isdigit()]
                    await cleanup_messages_via_userbot(chat_id, message_ids=message_ids)
                else:
                    n = int(param)
                    last_msg_id = int(parts[3]) if len(parts) > 3 else None
                    if last_msg_id:
                        await cleanup_messages_via_userbot(chat_id, last_msg_id=last_msg_id, n=n)
        except:
            pass

# ================= استارت یوزربات =================
async def start_userbot():
    await client.start()
    print("✅ Userbot ready and listening to bot commands...")
    await client.run_until_disconnected()
