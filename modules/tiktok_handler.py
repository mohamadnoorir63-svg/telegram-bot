import os
import asyncio
import uuid
import requests
import yt_dlp

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

SUDO_USERS = [8588347189]
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0 Safari/537.36"
)

video_store = {}


async def is_admin(update, context):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == "private":
        return True

    if user.id in SUDO_USERS:
        return True

    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        return member.status in ["administrator", "creator"]
    except Exception:
        return False


def resolve_url(url: str) -> str:
    if "vm.tiktok.com" in url or "vt.tiktok.com" in url:
        r = requests.get(
            url,
            allow_redirects=True,
            timeout=10,
            headers={"User-Agent": USER_AGENT}
        )
        return r.url
    return url


def _download_tiktok_video(url: str):
    file_key = str(uuid.uuid4())

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "format": "best[ext=mp4]/best",
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, f"{file_key}.%(ext)s"),
        "socket_timeout": 20,
        "retries": 3,
        "fragment_retries": 3,
        "http_headers": {
            "User-Agent": USER_AGENT,
            "Referer": "https://www.tiktok.com/"
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return info, filename


def _download_tiktok_audio(url: str):
    file_key = str(uuid.uuid4())

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "format": "bestaudio/best",
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, f"{file_key}.%(ext)s"),
        "socket_timeout": 20,
        "retries": 3,
        "fragment_retries": 3,
        "http_headers": {
            "User-Agent": USER_AGENT,
            "Referer": "https://www.tiktok.com/"
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return info, filename


def clean_file(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


async def tiktok_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    url = update.message.text.strip()

    if not any(x in url for x in ["tiktok.com", "vm.tiktok.com", "vt.tiktok.com"]):
        return

    if update.effective_chat.type != "private":
        if not await is_admin(update, context):
            return

    msg = await update.message.reply_text("⚡ در حال دانلود TikTok...")

    try:
        loop = asyncio.get_running_loop()
        url = await loop.run_in_executor(None, resolve_url, url)

        if "/photo/" in url:
            return await msg.edit_text("❌ عکس‌های TikTok فعلاً پشتیبانی نمی‌شوند.")

        info, video_path = await loop.run_in_executor(None, _download_tiktok_video, url)

        if not video_path or not os.path.exists(video_path):
            return await msg.edit_text("❌ ویدیو دانلود نشد.")

        video_id = str(uuid.uuid4())
        video_store[video_id] = {
            "url": url,
            "video": video_path
        }

        keyboard = []

        if update.effective_chat.type == "private":
            keyboard.append([
                InlineKeyboardButton(
                    "➕ افزودن به گروه",
                    url="https://t.me/AFGR63_bot?startgroup=true"
                )
            ])

        keyboard.append([
            InlineKeyboardButton(
                "🎵 دانلود صوتی",
                callback_data=f"tiktok_audio:{video_id}"
            )
        ])

        with open(video_path, "rb") as video_file:
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=video_file,
                caption=f"🎬 {info.get('title') or 'TikTok Video'}",
                reply_markup=InlineKeyboardMarkup(keyboard),
                supports_streaming=True,
                read_timeout=120,
                write_timeout=120,
                connect_timeout=60
            )

        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود TikTok:\n{e}")


async def tiktok_audio_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer("🎵 در حال آماده‌سازی صوت...")

    video_id = cq.data.split(":", 1)[1]
    data = video_store.get(video_id)

    if not data:
        return await cq.message.reply_text("❌ لینک پیدا نشد. دوباره لینک TikTok را بفرست.")

    url = data["url"]
    wait_msg = await cq.message.reply_text("⚡ در حال دانلود صوت...")

    audio_path = None

    try:
        loop = asyncio.get_running_loop()
        info, audio_path = await loop.run_in_executor(None, _download_tiktok_audio, url)

        if not audio_path or not os.path.exists(audio_path):
            return await wait_msg.edit_text("❌ فایل صوتی دانلود نشد.")

        with open(audio_path, "rb") as audio_file:
            await context.bot.send_audio(
                chat_id=cq.message.chat_id,
                audio=audio_file,
                caption="🎵 نسخه صوتی TikTok",
                title=info.get("title") or "TikTok Audio",
                read_timeout=120,
                write_timeout=120,
                connect_timeout=60
            )

        await wait_msg.delete()

    except Exception as e:
        await wait_msg.edit_text(f"❌ خطا در دانلود صوت:\n{e}")

    finally:
        clean_file(audio_path)
