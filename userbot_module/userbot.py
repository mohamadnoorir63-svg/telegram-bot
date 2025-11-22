# ================= هماهنگ سازی یوزربات با ربات اصلی =================

import os
import asyncio
import random
from telethon import TelegramClient, events, sessions
from datetime import datetime, timedelta
import json
from pytgcalls import PyTgClient
from pytgcalls.types.input_stream import AudioPiped, AudioVideoPiped

# ---------- یوزربات ----------
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")
BOT_USER_ID = int(os.environ.get("BOT_USER_ID"))

client = TelegramClient(sessions.StringSession(SESSION_STRING), API_ID, API_HASH)
pytgcalls = PyTgClient(client)

# ذخیره وضعیت پخش در هر چت
playing_in_chat = {}

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

# ================= مدیریت پخش در گروه =================
@client.on(events.NewMessage)
async def play_in_call(event):
    if event.sender_id not in SUDO_IDS:
        return

    chat_id = event.chat_id

    # پایان پخش
    if event.raw_text.lower() in ["تمام", "پایان", "stop"]:
        if playing_in_chat.get(chat_id):
            await pytgcalls.leave_group_call(chat_id)
            playing_in_chat[chat_id] = False
        return

    # ریپلای روی مدیا
    if event.is_reply:
        reply_msg = await event.get_reply_message()
        if reply_msg.audio or reply_msg.voice or reply_msg.video or reply_msg.document:
            file_path = await client.download_media(reply_msg)
            stream = AudioPiped(file_path)
            await pytgcalls.join_group_call(chat_id, stream)
            playing_in_chat[chat_id] = True

# ================= تگ کاربران با یوزربات =================
async def tag_users(chat_id, user_ids=None, random_count=None):
    try:
        members = await client.get_participants(chat_id)
        non_bots = [m for m in members if not m.bot]
        
        if random_count:
            non_bots = random.sample(non_bots, min(random_count, len(non_bots)))
        elif user_ids:
            non_bots = [m for m in non_bots if m.id in user_ids]
        
        mentions = [f"[{m.first_name}](tg://user?id={m.id})" for m in non_bots]
        chunk_size = 20
        
        for i in range(0, len(mentions), chunk_size):
            await client.send_message(
                chat_id,
                "👥 " + " ".join(mentions[i:i + chunk_size]),
                parse_mode="md",
                silent=True
            )
            await asyncio.sleep(1)
    except:
        pass

# ================= پاکسازی یوزربات =================
async def cleanup_via_userbot(chat_id, count=None, last_msg_id=None, mids=None):
    try:
        if mids:
            for mid in mids:
                try:
                    await client.delete_messages(chat_id, mid)
                except:
                    pass
                await asyncio.sleep(0.08)
            return

        if count:
            for mid in range(last_msg_id, max(1, last_msg_id - count), -1):
                try:
                    await client.delete_messages(chat_id, mid)
                except:
                    pass
                await asyncio.sleep(0.08)
            return

        for mid in range(last_msg_id, 1, -1):
            try:
                await client.delete_messages(chat_id, mid)
            except:
                pass
            await asyncio.sleep(0.08)
    except:
        pass

# ================= ارسال دستورات تنبیهی =================
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

    # ---------- تگ ----------
    if action == "tagall":
        await tag_users(chat_id)
    elif action.startswith("tagrandom"):
        count = 5
        if len(parts) >= 3 and parts[2].isdigit():
            count = int(parts[2])
        await tag_users(chat_id, random_count=count)
    elif action.startswith("taglist"):
        if len(parts) >= 3:
            ids = [int(x) for x in parts[2].split(",") if x.isdigit()]
        else:
            ids = None
        await tag_users(chat_id, user_ids=ids)

    # ---------- بن / آنبن ----------
    elif action == "ban":
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
    elif action == "unban":
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

    # ---------- پاکسازی ----------
    elif action == "cleanup":
        last_msg_id = int(parts[2])
        if len(parts) >= 4 and parts[3].isdigit():
            count = int(parts[3])
            await cleanup_via_userbot(chat_id, count=count, last_msg_id=last_msg_id)
            return
        if len(parts) >= 4 and "," in parts[3]:
            mids = [int(x) for x in parts[3].split(",") if x.isdigit()]
            await cleanup_via_userbot(chat_id, mids=mids)
            return
        await cleanup_via_userbot(chat_id, last_msg_id=last_msg_id)

# ---------- پینگ ----------
@client.on(events.NewMessage)
async def simple_ping(event):
    text = event.raw_text.lower()
    if text == "ping":
        await event.reply("✅ Userbot Online")

# ---------- لفت ----------
@client.on(events.NewMessage)
async def simple_left(event):
    text = event.raw_text.lower()
    if text == "left":
        try:
            chat_id = event.chat_id
            await client.send_message(chat_id, "👋 در حال لفت…")
            await client.delete_dialog(chat_id)
        except Exception as e:
            await event.reply(f"❌ خطا در لفت: {e}")

# ================= استارت یوزربات =================
async def start_userbot():
    await client.start()
    print("✅ Userbot ready and listening to bot commands...")
    await pytgcalls.start()
    await client.run_until_disconnected()

# ================= اجرا =================
if __name__ == "__main__":
    asyncio.run(start_userbot())
