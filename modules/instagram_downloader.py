import os
import asyncio
import uuid
import yt_dlp

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Chat
from telegram.ext import ContextTypes

SUDO_USERS = [8588347189]
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

INSTAGRAM_COOKIES = """\
# Netscape HTTP Cookie File
.instagram.com	TRUE	/	TRUE	1799977780	csrftoken	--d8oLwWArIVOTuxrKibqa
.instagram.com	TRUE	/	TRUE	1799687399	datr	47Q1aZceuWl7nLkf_Uzh_kVW
.instagram.com	TRUE	/	TRUE	1796663399	ig_did	615B02DC-3964-40ED-864D-5EDD6E7C4EA3
.instagram.com	TRUE	/	TRUE	1799687399	mid	aTW04wABAAHoKpxsaAJbAfLsgVU3
.instagram.com	TRUE	/	TRUE	1765732343	dpr	2
.instagram.com	TRUE	/	TRUE	1773193780	ds_user_id	79160628834
.instagram.com	TRUE	/	TRUE	1766022576	wd	360x683
.instagram.com	TRUE	/	TRUE	1796933591	sessionid	79160628834%3AtMYF1zDBj9tXx3%3A7%3AAYjlXAe8pz6DF9H0JRMzmLpz4PmyQSRhYqRixrTn5w
.instagram.com	TRUE	/	TRUE	0	rur	"CLN\05479160628834\0541796953780:01fe354b018be3558f1977c6d5d2af3c4df7b30c01a2b6405fc52893b2c404d3d3e6a3ae"
"""

video_store = {}


async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == Chat.PRIVATE:
        return True

    if user.id in SUDO_USERS:
        return True

    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        return member.status in ["administrator", "creator"]
    except Exception:
        return False


def make_cookie_file() -> str:
    cookie_path = os.path.join(DOWNLOAD_FOLDER, f"instagram_cookie_{uuid.uuid4()}.txt")
    with open(cookie_path, "w", encoding="utf-8") as f:
        f.write(INSTAGRAM_COOKIES.strip())
    return cookie_path


def clean_file(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def _download_instagram_video(url: str):
    file_key = str(uuid.uuid4())
    cookie_path = make_cookie_file()

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "noplaylist": False,
        "format": "best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, f"{file_key}_%(id)s.%(ext)s"),
        "cookiefile": cookie_path,
        "socket_timeout": 25,
        "retries": 3,
        "fragment_retries": 3,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            if not info:
                return []

            entries = info.get("entries") or [info]
            results = []

            for entry in entries:
                if not entry:
                    continue

                filename = ydl.prepare_filename(entry)

                if not os.path.exists(filename):
                    base = os.path.splitext(filename)[0]
                    mp4_path = base + ".mp4"
                    if os.path.exists(mp4_path):
                        filename = mp4_path

                if os.path.exists(filename):
                    results.append({
                        "id": entry.get("id") or str(uuid.uuid4()),
                        "title": entry.get("title") or "Instagram Video",
                        "url": url,
                        "file": filename,
                    })

            return results

    finally:
        clean_file(cookie_path)


def _download_instagram_audio(url: str):
    file_key = str(uuid.uuid4())
    cookie_path = make_cookie_file()

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "noplaylist": True,
        "format": "bestaudio/best",
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, f"{file_key}.%(ext)s"),
        "cookiefile": cookie_path,
        "socket_timeout": 25,
        "retries": 3,
        "fragment_retries": 3,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            if not info:
                return None, None

            filename = ydl.prepare_filename(info)

            if filename and os.path.exists(filename):
                return info, filename

            return info, None

    finally:
        clean_file(cookie_path)


async def instagram_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    chat = update.effective_chat
    chat_id = chat.id
    url = update.message.text.strip()

    if "instagram.com" not in url:
        return

    if chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        if not await is_admin(update, context):
            return

    msg = await update.message.reply_text("⚡ در حال دانلود از Instagram...")

    try:
        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(None, _download_instagram_video, url)

        if not results:
            return await msg.edit_text("❌ امکان دانلود این پست وجود ندارد.")

        sent_any = False

        for item in results:
            file_path = item["file"]

            if not os.path.exists(file_path):
                continue

            video_id = str(uuid.uuid4())
            video_store[video_id] = {
                "url": item["url"],
                "video": file_path
            }

            keyboard = []

            if chat.type == Chat.PRIVATE:
                keyboard.append([
                    InlineKeyboardButton(
                        "➕ افزودن به گروه",
                        url="https://t.me/AFGR63_bot?startgroup=true"
                    )
                ])

            keyboard.append([
                InlineKeyboardButton(
                    "🎵 دانلود صوتی",
                    callback_data=f"instagram_audio:{video_id}"
                )
            ])

            with open(file_path, "rb") as fvideo:
                await context.bot.send_video(
                    chat_id=chat_id,
                    video=fvideo,
                    caption=f"🎬 {item.get('title') or 'Instagram Video'}",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    supports_streaming=True,
                    read_timeout=120,
                    write_timeout=120,
                    connect_timeout=60
                )

            sent_any = True

        if sent_any:
            await msg.delete()
        else:
            await msg.edit_text("❌ فایل دانلود شد اما برای ارسال پیدا نشد.")

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود از اینستاگرام:\n{e}")


async def instagram_audio_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer("🎵 در حال آماده‌سازی صوت...")

    video_id = cq.data.split(":", 1)[1]
    data = video_store.get(video_id)

    if not data:
        return await cq.message.reply_text("❌ لینک پیدا نشد. دوباره لینک Instagram را بفرست.")

    url = data["url"]
    wait_msg = await cq.message.reply_text("⚡ در حال دانلود صوت...")

    audio_path = None

    try:
        loop = asyncio.get_running_loop()
        info, audio_path = await loop.run_in_executor(None, _download_instagram_audio, url)

        if not audio_path or not os.path.exists(audio_path):
            return await wait_msg.edit_text("❌ فایل صوتی دانلود نشد.")

        with open(audio_path, "rb") as faudio:
            await context.bot.send_audio(
                chat_id=cq.message.chat_id,
                audio=faudio,
                caption="🎵 نسخه صوتی Instagram",
                title=(info or {}).get("title") or "Instagram Audio",
                read_timeout=120,
                write_timeout=120,
                connect_timeout=60
            )

        await wait_msg.delete()

    except Exception as e:
        await wait_msg.edit_text(f"❌ خطا در دانلود صوت:\n{e}")

    finally:
        clean_file(audio_path)
