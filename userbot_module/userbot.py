# ================= هماهنگ سازی یوزربات با ربات اصلی =================

import os
import asyncio
import random
from telethon import TelegramClient, events, sessions
from datetime import datetime, timedelta
import json

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
        # ---------- پاکسازی کامل گروه با دستور مستقیم ----------

import time
from datetime import datetime

# ذخیره آخرین زمان پاکسازی
LAST_CLEAN_TIME = 0  # زمان یونیکس

# ---------- پاکسازی کامل گروه با دستور مستقیم ----------
@client.on(events.NewMessage)
async def clean_all_direct(event):
    global LAST_CLEAN_TIME

    text = event.raw_text.strip()
    sender_id = event.sender_id
    chat_id = event.chat_id

    if text != "پاکسازی کل گروه":
        return

    # ========== اجازه اجرا برای سودو ==========

import time
from datetime import datetime

# ذخیره آخرین زمان پاکسازی برای هر گروه
LAST_CLEAN_TIME = {}  # key = chat_id  , value = timestamp

# ---------- پاکسازی کامل گروه با دستور مستقیم ----------
@client.on(events.NewMessage)
async def clean_all_direct(event):

    text = event.raw_text.strip()
    sender_id = event.sender_id
    chat_id = event.chat_id

    if text != "پاکسازی کل گروه":
        return

    # ========== اجازه اجرا برای سودو ==========
    is_sudo = sender_id in SUDO_IDS

    # ========== اجازه اجرا برای مدیران گروه ==========
    is_admin = False
    try:
        perms = await client.get_permissions(chat_id, sender_id)
        is_admin = perms.is_admin
    except:
        pass

    # اگر نه سودو بود نه ادمین → اجازه ندارد
    if not (is_sudo or is_admin):
        return await event.reply("⛔ فقط مدیران گروه یا سودو میتوانند از این دستور استفاده کنند.")

    # ======================= محدودیت ۸ ساعت هر گروه =======================
    now = time.time()
    last_time = LAST_CLEAN_TIME.get(chat_id, 0)

    if now - last_time < 28800:  # ۸ ساعت = 28800 ثانیه
        remaining = int((28800 - (now - last_time)) // 3600)
        return await event.reply(
            f"⛔ در این گروه فقط هر ۸ ساعت یک‌بار قابل اجراست.\n"
            f"⏳ زمان باقی‌مانده تقریبی: **{remaining} ساعت**"
        )

    # ثبت زمان جدید فقط برای همین گروه
    LAST_CLEAN_TIME[chat_id] = now

    # ======================= پاکسازی =======================
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

        # گزارش نهایی
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
            "⛔ محدودیت: هر گروه هر ۸ ساعت یک‌بار\n"
            "━━━━━━━━━━━━━━"
        )

        await client.send_message(chat_id, report)

    except Exception as e:
        await event.reply(f"❌ خطا در پاکسازی کامل: {e}")
# ================= پاکسازی یوزربات =================

async def cleanup_via_userbot(chat_id, count=None, last_msg_id=None, mids=None):
    try:
        # حالت ۳: لیست message_id ها
        if mids:
            for mid in mids:
                try:
                    await client.delete_messages(chat_id, mid)
                except:
                    pass
                await asyncio.sleep(0.08)
            return

        # حالت ۱: پاکسازی عددی
        if count:
            for mid in range(last_msg_id, max(1, last_msg_id - count), -1):
                try:
                    await client.delete_messages(chat_id, mid)
                except:
                    pass
                await asyncio.sleep(0.08)
            return

        # حالت ۲: پاکسازی کامل
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
        # اگر آرگومان چهارم عدد است → پاکسازی عددی
        if len(parts) >= 4 and parts[3].isdigit():
            count = int(parts[3])
            await cleanup_via_userbot(chat_id, count=count, last_msg_id=last_msg_id)
            return
        # اگر لیست بود → پاکسازی انتخابی
        if len(parts) >= 4 and "," in parts[3]:
            mids = [int(x) for x in parts[3].split(",") if x.isdigit()]
            await cleanup_via_userbot(chat_id, mids=mids)
            return
        # در غیر این صورت → پاکسازی کامل
        await cleanup_via_userbot(chat_id, last_msg_id=last_msg_id)
      # ====================== START TikTok & Instagram Downloader ======================

import os
import requests
from telethon import events, Button
import yt_dlp

# پوشه ذخیره‌سازی
os.makedirs("downloads", exist_ok=True)
MEDIA_MAP = {}  # key = message_id, value = {"file": path, "title": title}

# ---------- دانلود رسانه TikTok و Instagram ----------
@client.on(events.NewMessage(pattern=r"^(https?://(www\.)?(tiktok\.com|vm\.tiktok\.com|vt\.tiktok\.com|instagram\.com/p/|instagr\.am/p/).+)"))
async def media_downloader(event):
    url = event.raw_text.strip()
    chat_id = event.chat_id
    msg = await event.reply("⬇️ در حال پردازش رسانه ...")

    # ریدایرکت لینک کوتاه TikTok
    if "vm.tiktok.com" in url or "vt.tiktok.com" in url:
        try:
            resp = requests.get(url, allow_redirects=True)
            url = resp.url
        except Exception as e:
            await msg.edit(f"❌ خطا در ریدایرکت لینک TikTok: {e}")
            return

    # عکس TikTok
    if "/photo/" in url:
        try:
            filename = f"downloads/{url.split('/')[-1]}.jpg"
            r = requests.get(url)
            with open(filename, "wb") as f:
                f.write(r.content)

            await client.send_file(
                chat_id,
                filename,
                caption="🖼 عکس TikTok"
            )
            os.remove(filename)
            await msg.delete()
        except Exception as e:
            await msg.edit(f"❌ خطا در دانلود عکس TikTok: {e}")
        return

    # دانلود ویدیو (TikTok یا Instagram)
    ydl_opts = {
        "format": "mp4",
        "outtmpl": "downloads/%(id)s.%(ext)s",
        "quiet": True,
        "noplaylist": True,
        "merge_output_format": "mp4"
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        sent_msg = await client.send_file(
            chat_id,
            filename,
            caption=f"🎬 {info.get('title', 'Media Video')}",
            buttons=[
                [Button.inline("🎵 دانلود صوتی", data=f"download_music|{filename}")]
            ]
        )
        MEDIA_MAP[filename] = filename
        os.remove(filename)
        await msg.delete()

    except Exception as e:
        await msg.edit(f"❌ خطا در دانلود ویدیو: {e}")
        print(e)

# ---------- هندل دکمه دانلود صوتی ----------
@client.on(events.CallbackQuery(pattern=r"download_music\|(.+)"))
async def download_music(event):
    video_path = event.pattern_match.group(1)
    mp3_path = video_path.rsplit(".", 1)[0] + ".mp3"

    await event.answer("⬇️ در حال استخراج صوت ...", alert=True)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": mp3_path,
        "quiet": True,
        "postprocessors": [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_path])

        await client.send_file(event.chat_id, mp3_path, caption="🎵 موزیک ویدیو")
        os.remove(mp3_path)

    except Exception as e:
        await event.reply(f"❌ خطا در استخراج موزیک: {e}")
        print(e)

# ====================== END TikTok & Instagram Downloader ======================

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
    await client.run_until_disconnected()

# ================= اجرا =================
if __name__ == "__main__":
    import asyncio
    
