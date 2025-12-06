# ================= یوزربات مستقل با موزیک =================

import os
import asyncio
import time
from datetime import datetime, timedelta
import json
from telethon import TelegramClient, events, sessions
import yt_dlp

# ---------- متغیرهای یوزربات ----------
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")

SUDO_IDS = [8588347189]  # آی‌دی خودت

client = TelegramClient(sessions.StringSession(SESSION_STRING), API_ID, API_HASH)

# ---------- فایل هشدارها ----------
WARN_FILE = "warnings.json"
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

# ---------- زمان آخرین پاکسازی ----------
LAST_CLEAN_TIME = {}

# ---------- پاکسازی گروه ----------
@client.on(events.NewMessage(pattern="پاکسازی کل گروه"))
async def clean_all_direct(event):
    sender_id = event.sender_id
    chat_id = event.chat_id

    is_sudo = sender_id in SUDO_IDS
    is_admin = False
    try:
        perms = await client.get_permissions(chat_id, sender_id)
        is_admin = perms.is_admin
    except:
        pass

    if not (is_sudo or is_admin):
        return await event.reply("⛔ فقط مدیران گروه یا سودو میتوانند از این دستور استفاده کنند.")

    now = time.time()
    last_time = LAST_CLEAN_TIME.get(chat_id, 0)
    if now - last_time < 28800:  # ۸ ساعت
        remaining = int((28800 - (now - last_time)) // 3600)
        return await event.reply(f"⛔ فقط هر ۸ ساعت یک‌بار می‌توانید پاکسازی کنید.\n⏳ تقریبا {remaining} ساعت باقی‌مانده")

    LAST_CLEAN_TIME[chat_id] = now

    try:
        await event.reply("🧹 در حال پاک‌سازی سریع گروه …")
        batch = []
        deleted_count = 0
        async for msg in client.iter_messages(chat_id):
            batch.append(msg.id)
            if len(batch) >= 100:
                try:
                    await client.delete_messages(chat_id, batch)
                    deleted_count += len(batch)
                except:
                    pass
                batch = []
                await asyncio.sleep(0.02)
        if batch:
            try:
                await client.delete_messages(chat_id, batch)
                deleted_count += len(batch)
            except:
                pass

        now_str = datetime.now().strftime("%Y-%m-%d | %H:%M:%S")
        admin = await client.get_entity(sender_id)
        role = "سودو" if is_sudo else "مدیر گروه"
        report = (
            "📦 **گزارش پاکسازی کامل گروه**\n"
            "━━━━━━━━━━━━━━\n"
            f"👤 اجرا توسط: `{admin.first_name}` (ID: {sender_id})\n"
            f"🌐 نقش: **{role}**\n"
            f"🗑 تعداد پیام‌های حذف‌شده: **{deleted_count}**\n"
            f"⏰ زمان اجرا: `{now_str}`\n"
            "━━━━━━━━━━━━━━"
        )
        await client.send_message(chat_id, report)

    except Exception as e:
        await event.reply(f"❌ خطا در پاکسازی: {e}")

# ---------- دانلود موزیک ----------
async def download_music(query):
    download_path = f"downloads/{query}.mp3"
    os.makedirs("downloads", exist_ok=True)

    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'outtmpl': download_path,
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    search_url = f"ytsearch1:{query}"
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([search_url])

    return download_path

# ---------- فرمان موزیک مستقل ----------
@client.on(events.NewMessage(pattern=r"^/music (.+)"))
async def music_command(event):
    query = event.pattern_match.group(1).strip()
    chat_id = event.chat_id
    msg = await client.send_message(chat_id, f"🎵 در حال دانلود: {query} ...")
    try:
        file_path = await download_music(query)
        await client.send_file(chat_id, file_path, caption=f"🎶 {query}")
        os.remove(file_path)
        await msg.delete()
    except Exception as e:
        await msg.edit(f"❌ خطا در دانلود موزیک: {e}")

# ---------- لفت ----------
@client.on(events.NewMessage(pattern="left"))
async def simple_left(event):
    try:
        chat_id = event.chat_id
        await client.send_message(chat_id, "👋 در حال لفت…")
        await client.delete_dialog(chat_id)
    except Exception as e:
        await event.reply(f"❌ خطا در لفت: {e}")

# ================= استارت یوزربات =================
async def start_userbot():
    await client.start()
    print("✅ Userbot ready and listening...")
    await client.run_until_disconnected()

# ================= اجرا =================
if __name__ == "__main__":
    asyncio.run(start_userbot())
