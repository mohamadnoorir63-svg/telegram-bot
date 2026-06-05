# modules/tiktok_handler.py
import os
import shutil
import subprocess
import requests
import yt_dlp
import asyncio
import uuid

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

SUDO_USERS = [8588347189]
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

video_store = {}


async def is_admin(update, context):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == "private" or user.id in SUDO_USERS:
        return True

    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        return member.status in ["administrator", "creator"]
    except:
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
        "noplaylist": True,
        "format": "bv*+ba/best",
        "merge_output_format": "mp4",
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, f"{file_key}.%(ext)s"),
        "http_headers": {
            "User-Agent": USER_AGENT,
            "Referer": "https://www.tiktok.com/"
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

        if not filename.endswith(".mp4"):
            base = os.path.splitext(filename)[0]
            mp4 = base + ".mp4"
            if os.path.exists(mp4):
                filename = mp4

        return info, filename


def _download_tiktok_audio(url: str):
    file_key = str(uuid.uuid4())
    outtmpl = os.path.join(DOWNLOAD_FOLDER, f"{file_key}.%(ext)s")

    ydl_opts = {
        "quiet": True,
        "noplaylist": True,
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "http_headers": {
            "User-Agent": USER_AGENT,
            "Referer": "https://www.tiktok.com/"
        },
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        mp3_path = os.path.join(DOWNLOAD_FOLDER, f"{file_key}.mp3")
        return info, mp3_path


async def tiktok_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    url = update.message.text.strip()

    if not any(x in url for x in ["tiktok.com", "vm.tiktok.com", "vt.tiktok.com"]):
        return

    if update.effective_chat.type != "private":
        allowed = await is_admin(update, context)
        if not allowed:
            return

    msg = await update.message.reply_text("⬇️ در حال دانلود TikTok ...")

    try:
        loop = asyncio.get_running_loop()
        url = await loop.run_in_executor(None, resolve_url, url)

        if "/photo/" in url:
            await msg.edit_text("❌ عکس‌های TikTok فعلاً پشتیبانی نمی‌شوند.")
            return

        info, filename = await loop.run_in_executor(None, _download_tiktok_video, url)

        if not filename or not os.path.exists(filename):
            await msg.edit_text("❌ ویدیو دانلود نشد.")
            return

        video_id = str(uuid.uuid4())
        video_store[video_id] = {
            "url": url,
            "video": filename
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

        await context.bot.send_video(
            chat_id=update.effective_chat.id,
            video=open(filename, "rb"),
            caption=f"🎬 {info.get('title', 'TikTok Video')}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            supports_streaming=True
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
        return await cq.message.reply_text("❌ لینک یا فایل پیدا نشد. دوباره ویدیو را بفرست.")

    url = data["url"]
    wait_msg = await cq.message.reply_text("🎵 در حال دانلود صوت...")

    try:
        loop = asyncio.get_running_loop()
        info, mp3_path = await loop.run_in_executor(None, _download_tiktok_audio, url)

        if not os.path.exists(mp3_path):
            return await wait_msg.edit_text("❌ فایل صوتی ساخته نشد. مطمئن شو ffmpeg نصب است.")

        await context.bot.send_audio(
            chat_id=cq.message.chat_id,
            audio=open(mp3_path, "rb"),
            caption="🎵 نسخه صوتی TikTok",
            title=info.get("title", "TikTok Audio")
        )

        await wait_msg.delete()

    except Exception as e:
        await wait_msg.edit_text(f"❌ خطا در دانلود صوت:\n{e}")

    finally:
        try:
            if "mp3_path" in locals() and os.path.exists(mp3_path):
                os.remove(mp3_path)
        except:
            pass
