# modules/music_handler.py
import os
import shutil
import subprocess
import yt_dlp
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

async def convert_to_mp3(video_path: str) -> str:
    mp3_path = video_path.rsplit(".", 1)[0] + ".mp3"
    if not shutil.which("ffmpeg"):
        return None
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-ab", "192k", "-ar", "44100",
        "-f", "mp3", mp3_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return mp3_path

# ---------------------
# مرحله 1: جستجوی موزیک
# ---------------------
async def music_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    query = update.message.text.replace("/موزیک", "").strip()
    chat_id = update.effective_chat.id
    msg = await update.message.reply_text(f"🔎 در حال جستجوی '{query}' ...")

    ydl_opts = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "extract_flat": "in_playlist",
        "skip_download": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android"]
            }
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch3:{query}", download=False)

        results = info.get("entries", [])
        if not results:
            await msg.edit_text("❌ نتیجه‌ای پیدا نشد.")
            return

        # ساخت دکمه‌ها
        buttons = []
        for i, entry in enumerate(results, 1):
            buttons.append([InlineKeyboardButton(
                f"{i}. {entry.get('title')}",
                callback_data=f"music_select:{entry['id']}"
            )])
        
        markup = InlineKeyboardMarkup(buttons)
        await msg.edit_text("🎵 یکی از نتایج زیر را انتخاب کنید:", reply_markup=markup)

    except Exception as e:
        await msg.edit_text(f"❌ خطا در جستجوی موزیک:\n{e}")

# ---------------------
# مرحله 2: دانلود بعد از انتخاب
# ---------------------
async def music_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    video_id = query.data.split(":")[1]
    chat_id = query.message.chat.id
    msg = await query.message.edit_text("⬇️ در حال دانلود و تبدیل به MP3 ...")

    outtmpl = os.path.join(DOWNLOAD_FOLDER, f"%(id)s_{uuid.uuid4().hex}.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "quiet": True,
        "noplaylist": True,
        "merge_output_format": "mp3",
        "extractor_args": {
            "youtube": {"player_client": ["android"]}
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=True)
            filename = ydl.prepare_filename(info)

        mp3_path = await convert_to_mp3(filename)
        if mp3_path and os.path.exists(mp3_path):
            await context.bot.send_audio(chat_id, mp3_path, caption=f"🎵 {info.get('title')}")
            os.remove(mp3_path)
        os.remove(filename)
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود موزیک:\n{e}")
