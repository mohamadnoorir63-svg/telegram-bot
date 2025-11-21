# ================= هماهنگ سازی یوزربات با ربات اصلی =================

import os
import asyncio
import random
from telethon import TelegramClient, events, sessions
from datetime import datetime, timedelta
import json

# ---------- یوزربات ----------
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH"))
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

# ================= ارسال دستورات تنبیهی روی یوزربات =================
async def punish_via_userbot(chat_id, user_id, action="ban", seconds=None):
    try:
        if action == "ban":
            await client.edit_permissions(chat_id, user_id, view_messages=False)

        elif action == "unban":
            await client.edit_permissions(chat_id, user_id, view_messages=True)

        elif action == "mute":
            until = datetime.utcnow() + timedelta(seconds=seconds) if seconds else None
            await client.edit_permissions(chat_id, user_id, send_messages=False, until_date=until)

        elif action == "unmute":
            await client.edit_permissions(chat_id, user_id, send_messages=True)

    except:
        pass

# ================= هندلر واحد برای تمام پیام‌ها =================
@client.on(events.NewMessage)
async def all_handlers(event):
    text = event.raw_text.lower()
    sender = await event.get_sender()

    # -------------------------------------------------------
    # فرمان‌های ربات اصلی (handle_commands قبلی)
    # -------------------------------------------------------
    if sender.id == BOT_USER_ID:
        parts = event.raw_text.split("|")
        if len(parts) >= 2:
            action = parts[0].strip().lower()
            chat_id = int(parts[1])

            if action == "tagall":
                return await tag_users(chat_id)

            elif action.startswith("tagrandom"):
                count = int(parts[2]) if len(parts) >= 3 and parts[2].isdigit() else 5
                return await tag_users(chat_id, random_count=count)

            elif action.startswith("taglist"):
                ids = [int(x) for x in parts[2].split(",")] if len(parts) >= 3 else None
                return await tag_users(chat_id, user_ids=ids)

            elif action == "ban":
                target = parts[2].strip()
                user_id = int(target) if target.isdigit() else None
                if target.startswith("@"):
                    try:
                        user_id = (await client.get_entity(target)).id
                    except:
                        pass
                if user_id:
                    return await punish_via_userbot(chat_id, user_id, action="ban")

            elif action == "unban":
                target = parts[2].strip()
                user_id = int(target) if target.isdigit() else None
                if target.startswith("@"):
                    try:
                        user_id = (await client.get_entity(target)).id
                    except:
                        pass
                if user_id:
                    return await punish_via_userbot(chat_id, user_id, action="unban")

            elif action == "cleanup":
                last_msg_id = int(parts[2])

                if len(parts) >= 4 and parts[3].isdigit():
                    return await cleanup_via_userbot(chat_id, count=int(parts[3]), last_msg_id=last_msg_id)

                if len(parts) >= 4 and "," in parts[3]:
                    mids = [int(x) for x in parts[3].split(",") if x.isdigit()]
                    return await cleanup_via_userbot(chat_id, mids=mids)

                return await cleanup_via_userbot(chat_id, last_msg_id=last_msg_id)

    # -------------------------------------------------------
    # پینگ (simple_ping)
    # -------------------------------------------------------
    if text == "ping":
        return await event.reply("✅ Userbot Online")

    # -------------------------------------------------------
    # لفت (simple_left)
    # -------------------------------------------------------
    if text == "left":
        try:
            await event.reply("👋 در حال لفت…")
            await client.delete_dialog(event.chat_id)
        except Exception as e:
            await event.reply(f"❌ خطا در لفت: {e}")

# ================= استارت یوزربات =================
async def start_userbot():
    await client.start()
    print("✅ Userbot ready and listening to bot commands...")
    await client.run_until_disconnected()

# ================= اجرا =================
if __name__ == "__main__":
    asyncio.run(start_userbot())
