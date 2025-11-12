import os
import asyncio
import json
import random
from datetime import datetime, timedelta
from telethon import TelegramClient, events, sessions
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

# ================= ⚙️ تنظیمات یوزربات =================
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")
BOT_USER_ID = int(os.environ.get("BOT_USER_ID"))
SUDO_IDS = [8588347189]

client = TelegramClient(sessions.StringSession(SESSION_STRING), API_ID, API_HASH)

# فایل هشدارها
WARN_FILE = "warnings.json"
if not os.path.exists(WARN_FILE):
    with open(WARN_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

# ================= 📁 توابع کمکی =================
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
    members = await client.get_participants(chat_id)
    non_bots = [m for m in members if not m.bot]

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

# ================= پاکسازی پیام‌ها با یوزربات =================
MAX_BULK = 10000
BATCH_SIZE = 20
SLEEP_SEC = 0.2

async def _delete_messages_userbot(chat_id: int, mids: list[int]) -> int:
    if not client or not mids:
        return 0
    deleted = 0
    for i in range(0, len(mids), BATCH_SIZE):
        batch = mids[i:i + BATCH_SIZE]
        try:
            await client.delete_messages(chat_id, batch)
            deleted += len(batch)
        except:
            continue
        await asyncio.sleep(SLEEP_SEC)
    return deleted

# ================= بررسی دسترسی کاربران =================
async def _has_access(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> bool:
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except:
        return False

# ================= دستور پاکسازی =================
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

    if text in ("پاکسازی", "clean"):
        try:
            messages = [m.id for m in await client.get_messages(chat.id, limit=MAX_BULK)]
            deleted = await _delete_messages_userbot(chat.id, messages)
            action_type = "🧼 پاکسازی کامل توسط یوزربات"
        except Exception as e:
            return await msg.reply_text(f"⚠️ خطا در یوزربات: {e}")

    elif msg.reply_to_message and (text.startswith("پاک") or text.startswith("حذف")):
        target = msg.reply_to_message.from_user
        try:
            msgs = await client.get_messages(chat.id, limit=MAX_BULK)
            messages = [m.id for m in msgs if m.sender_id == target.id]
            deleted = await _delete_messages_userbot(chat.id, messages)
            action_type = f"🧑‍💻 حذف پیام‌های {target.first_name} توسط یوزربات"
        except Exception as e:
            return await msg.reply_text(f"⚠️ خطا در یوزربات: {e}")

    elif text.startswith("حذف") or text.startswith("پاک"):
        try:
            n = int(args[0]) if args else int(text.split()[1])
        except:
            return await msg.reply_text("⚙️ فرمت درست: حذف 100")
        n = max(1, min(n, MAX_BULK))
        try:
            msgs = await client.get_messages(chat.id, limit=n)
            messages = [m.id for m in msgs]
            deleted = await _delete_messages_userbot(chat.id, messages)
            action_type = f"🧹 حذف عددی {n} پیام توسط یوزربات"
        except Exception as e:
            return await msg.reply_text(f"⚠️ خطا در یوزربات: {e}")

    else:
        return

    try:
        await msg.delete()
    except:
        pass

    await asyncio.sleep(0.5)
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

# ================= دریافت فرمان‌ها از ربات اصلی =================
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
        await tag_users(chat_id)
    elif action.startswith("tagrandom"):
        count = 5
        if len(parts) == 3 and parts[2].isdigit():
            count = int(parts[2])
        await tag_users(chat_id, random_count=count)
    elif action.startswith("taglist"):
        ids = [int(x) for x in parts[2].split(",") if x.isdigit()] if len(parts) > 2 else None
        await tag_users(chat_id, user_ids=ids)
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

# ================= ثبت هندلرهای پاکسازی در ربات اصلی =================
def register_cleanup_handlers(application):
    from telegram.ext import CommandHandler, MessageHandler, filters
    application.add_handler(CommandHandler("clean", funny_cleanup))
    application.add_handler(
        MessageHandler(
            (filters.TEXT & ~filters.COMMAND)
            & filters.Regex(r"^(?:پاکسازی|پاک(?:\s+\d+)?|حذف(?:\s+\d+)?)$"),
            funny_cleanup
        )
    )
