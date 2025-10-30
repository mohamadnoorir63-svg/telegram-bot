# userbot.py
# نسخه فارسی، کامل و ایمن

import os
import asyncio
import json
from datetime import datetime, timedelta
from telethon import TelegramClient, events, errors, functions
from telethon.sessions import StringSession
from telethon.tl.types import ChatBannedRights

# -----------------------------------------------
# 🧠 تنظیمات اتصال
# -----------------------------------------------
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION = os.getenv("SESSION_STRING", "")
OWNER_IDS = {7089376754}  # 👈 آیدی تو

if not API_ID or not API_HASH:
    raise SystemExit("❌ API_ID یا API_HASH تنظیم نشده‌اند.")

# ساخت اتصال یوزربات
client = TelegramClient(StringSession(SESSION) if SESSION else "userbot.session", API_ID, API_HASH)

# فایل ذخیره سکوت‌ها
MUTES_FILE = "userbot_mutes.json"
if not os.path.exists(MUTES_FILE):
    with open(MUTES_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

def load_mutes():
    try:
        with open(MUTES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_mutes(data):
    try:
        with open(MUTES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("[SAVE ERROR]", e)

# -----------------------------------------------
# ⚙️ ابزارهای کمکی
# -----------------------------------------------
def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

nuke_task = {"running": False, "cancel": False}

# -----------------------------------------------
# 🧩 دستورات
# -----------------------------------------------
@client.on(events.NewMessage(pattern=r"^پینگ$"))
async def ping_handler(event):
    await event.reply("🏓 یوزربات فعاله ✅")

@client.on(events.NewMessage(pattern=r"^نابود(?:\s+(\d+))?$"))
async def nuke_handler(event):
    sender = await event.get_sender()
    if sender.id not in OWNER_IDS:
        return await event.reply("🚫 شما مجوز اجرای این فرمان را ندارید.")

    m = event.pattern_match.group(1)
    limit = int(m) if m else 5000
    msg = await event.reply(f"🔥 آماده حذف تا {limit} پیام...")

    nuke_task["running"] = True
    nuke_task["cancel"] = False

    try:
        messages = await client.get_messages(event.chat_id, limit=limit)
        if not messages:
            await msg.edit("ℹ️ هیچ پیامی برای حذف نیست.")
            return

        ids = [m.id for m in messages]
        total = len(ids)
        deleted = 0
        for batch in chunks(ids, 100):
            if nuke_task["cancel"]:
                await msg.edit(f"⛔ عملیات متوقف شد ({deleted}/{total})")
                return
            await client.delete_messages(event.chat_id, batch, revoke=True)
            deleted += len(batch)
            await msg.edit(f"🧹 حذف شد: {deleted}/{total}")
            await asyncio.sleep(0.25)
        await msg.edit(f"✅ پاکسازی کامل شد ({deleted} پیام).")
    except Exception as e:
        await msg.edit(f"⚠️ خطا: {e}")
    finally:
        nuke_task["running"] = False

@client.on(events.NewMessage(pattern=r"^توقف$"))
async def stop_nuke(event):
    if nuke_task["running"]:
        nuke_task["cancel"] = True
        await event.reply("⛔ عملیات حذف متوقف شد.")
    else:
        await event.reply("ℹ️ عملیات فعالی در حال انجام نیست.")

@client.on(events.NewMessage(pattern=r"^بن$"))
async def ban_user(event):
    if not event.is_reply:
        return await event.reply("🔹 روی پیام فرد ریپلای کن و بن بزن.")
    sender = await event.get_sender()
    if sender.id not in OWNER_IDS:
        return await event.reply("🚫 مجوز نداری.")
    reply = await event.get_reply_message()
    uid = reply.sender_id
    rights = ChatBannedRights(until_date=None, view_messages=True)
    await client(functions.channels.EditBannedRequest(event.chat_id, uid, rights))
    await event.reply("⛔ کاربر بن شد.")

@client.on(events.NewMessage(pattern=r"^سکوت(?:\s+(\d+))?(?:\s*(ثانیه|دقیقه))?$"))
async def mute_user(event):
    if not event.is_reply:
        return await event.reply("🔹 روی پیام فرد ریپلای کن و بنویس: سکوت [زمان]")
    reply = await event.get_reply_message()
    uid = reply.sender_id
    num = event.pattern_match.group(1)
    unit = event.pattern_match.group(2) or ""
    sec = None
    if num:
        sec = int(num) * (60 if "دقیقه" in unit else 1)
    until = datetime.utcnow() + timedelta(seconds=sec) if sec else None
    rights = ChatBannedRights(until_date=until, send_messages=True)
    await client(functions.channels.EditBannedRequest(event.chat_id, uid, rights))
    await event.reply(f"🤐 {reply.sender.first_name} ساکت شد.")

@client.on(events.NewMessage(pattern=r"^حذف سکوت(?: همه)?$"))
async def unmute_user(event):
    text = event.raw_text
    if "همه" in text:
        mutes = load_mutes()
        cid = str(event.chat_id)
        if cid in mutes:
            for uid in list(mutes[cid].keys()):
                rights = ChatBannedRights(send_messages=False)
                await client(functions.channels.EditBannedRequest(event.chat_id, int(uid), rights))
            await event.reply("🔊 همه کاربران از سکوت خارج شدند.")
            mutes[cid] = {}
            save_mutes(mutes)
        else:
            await event.reply("ℹ️ سکوتی ثبت نشده.")
        return

    if not event.is_reply:
        return await event.reply("🔹 روی پیام فرد ریپلای کن و بنویس: حذف سکوت")
    reply = await event.get_reply_message()
    uid = reply.sender_id
    rights = ChatBannedRights(send_messages=False)
    await client(functions.channels.EditBannedRequest(event.chat_id, uid, rights))
    await event.reply("🔊 سکوت کاربر برداشته شد.")

@client.on(events.NewMessage(pattern=r"^اخطار$"))
async def warn_user(event):
    if not event.is_reply:
        return await event.reply("🔹 روی پیام فرد ریپلای کن و بنویس: اخطار")
    reply = await event.get_reply_message()
    await event.reply(f"⚠️ اخطار به {reply.sender.first_name} داده شد.")

# -----------------------------------------------
# 🚀 اجرای اصلی
# -----------------------------------------------
async def start_userbot():
    print("🔌 شروع Userbot ...")
    await client.start()
    me = await client.get_me()
    print(f"✅ یوزربات آنلاین شد: {me.first_name} ({me.id})")
    await client.run_until_disconnected()
