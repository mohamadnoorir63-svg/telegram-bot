# ================= هماهنگ سازی یوزربات با ربات اصلی =================

import os
import asyncio
import random
from telethon import TelegramClient, events, sessions
from datetime import datetime, timedelta
import json
from collections import deque, defaultdict
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

# ---------- یوزربات ----------
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")
BOT_USER_ID = int(os.environ.get("BOT_USER_ID"))

client = TelegramClient(sessions.StringSession(SESSION_STRING), API_ID, API_HASH)

# ---------- فایل هشدارها ----------
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
                "👥 " + " ".join(mentions),
                parse_mode="md",
                silent=True
            )
            await asyncio.sleep(1)
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
            until = None
            if seconds:
                until = datetime.utcnow() + timedelta(seconds=seconds)
            await client.edit_permissions(chat_id, user_id, send_messages=False, until_date=until)
        elif action == "unmute":
            await client.edit_permissions(chat_id, user_id, send_messages=True)
    except:
        pass

# ================= بافر پیام‌ها برای پاکسازی =================
MAX_BULK = 10000
TRACK_BUFFER = 600
track_map: dict[int, deque] = defaultdict(lambda: deque(maxlen=TRACK_BUFFER))

async def track_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if msg and msg.from_user and update.effective_chat.type in ("group", "supergroup"):
        track_map[update.effective_chat.id].append((msg.message_id, msg.from_user.id))

# ================= بررسی دسترسی =================
async def _has_access(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> bool:
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except:
        return False

# ================= حذف پیام‌ها با ربات یا یوزربات =================
async def _delete_messages_userbot(chat_id: int, mids: list[int]):
    if not client:
        return 0
    deleted = 0
    for mid in mids:
        try:
            await client.delete_messages(chat_id, [mid])
            deleted += 1
        except:
            continue
        await asyncio.sleep(0.01)
    return deleted

async def _delete_messages(context, chat_id: int, mids: list[int]):
    deleted = 0
    for mid in mids:
        try:
            await context.bot.delete_message(chat_id, mid)
            deleted += 1
        except:
            continue
        await asyncio.sleep(0.05)
    return deleted

async def _delete_last_n(context, chat_id: int, last_msg_id: int, n: int):
    start = max(1, last_msg_id - n)
    mids = list(range(last_msg_id, start - 1, -1))
    if client:
        return await _delete_messages_userbot(chat_id, mids)
    else:
        return await _delete_messages(context, chat_id, mids)

async def _delete_by_user_from_buffer(context, chat_id: int, user_id: int):
    mids = [mid for mid, uid in reversed(track_map.get(chat_id, [])) if uid == user_id]
    if client:
        return await _delete_messages_userbot(chat_id, mids)
    else:
        return await _delete_messages(context, chat_id, mids)

# ================= دستور اصلی پاکسازی =================
async def funny_cleanup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user
    text = (msg.text or "").strip().lower()
    args = context.args

    if chat.type not in ("group", "supergroup"):
        return await msg.reply_text("🚫 این دستور فقط در گروه‌ها قابل استفاده است.")

    if not await _has_access(context, chat.id, user.id):
        return await msg.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    deleted = 0
    action_type = "نامشخص"

    # پاکسازی کامل
    if text in ("پاکسازی", "clean"):
        mids = list(range(msg.message_id, 0, -1))
        deleted = await _delete_messages_userbot(chat.id, mids) if client else await _delete_messages(context, chat.id, mids)
        action_type = "🧼 پاکسازی کامل از اولین تا آخرین پیام"

    # حذف پیام‌های فرد خاص
    elif msg.reply_to_message and (text.startswith("پاک") or text.startswith("حذف")):
        target = msg.reply_to_message.from_user
        deleted = await _delete_by_user_from_buffer(context, chat.id, target.id)
        action_type = f"🧑‍💻 حذف پیام‌های {target.first_name}"

    # حذف عددی
    elif text.startswith("حذف") or text.startswith("پاک"):
        try:
            n = int(args[0]) if args else int(text.split()[1])
        except:
            return await msg.reply_text("⚙️ فرمت درست: حذف 100")
        n = max(1, min(n, MAX_BULK))
        deleted = await _delete_last_n(context, chat.id, msg.message_id, n)
        action_type = f"🧹 حذف عددی {n} پیام"

    # حذف خود دستور
    try:
        await msg.delete()
    except:
        pass

    time_now = datetime.now().strftime("%H:%M:%S")
    report = (
        f"✅ <b>گزارش پاکسازی</b>\n\n"
        f"{action_type}\n"
        f"📦 پیام‌های حذف‌شده: <b>{deleted}</b>\n"
        f"👤 دستوردهنده: <b>{user.first_name}</b>\n"
        f"🕓 ساعت اجرا: <code>{time_now}</code>"
    )
    try:
        await context.bot.send_message(chat.id, report, parse_mode="HTML")
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

    # ---------- تگ همه ----------
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

    # ---------- هماهنگ سازی بن ----------
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

# ================= استارت یوزربات =================
async def start_userbot():
    await client.start()
    print("✅ Userbot ready and listening to bot commands...")
    await client.run_until_disconnected()
