# modules/soundcloud_handler.py
import os
import shutil
import subprocess
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

async def convert_to_mp3(video_path: str) -> str:
    """تبدیل ویدیو/آهنگ به MP3"""
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

# ------------------------------
# جستجو در SoundCloud
# ------------------------------
async def soundcloud_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    chat_id = update.effective_chat.id

    if not text.startswith(("آهنگ ", "موزیک ")):
        return

    query = text.split(" ", 1)[1].strip()
    if not query:
        await update.message.reply_text("❌ لطفاً نام آهنگ را وارد کنید.")
        return

    msg = await update.message.reply_text("🔍 در حال جستجو در SoundCloud...")

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # جستجو با scsearch
            info = ydl.extract_info(f"scsearch5:{query}", download=False)
            if not info or "entries" not in info or not info["entries"]:
                await msg.edit_text("❌ آهنگ پیدا نشد.")
                return

            # ساخت دکمه‌ها برای 5 نتیجه اول
            keyboard = []
            for i, track in enumerate(info["entries"][:5], start=1):
                title = track.get("title", "SoundCloud")
                url = track.get("webpage_url")
                keyboard.append([InlineKeyboardButton(f"{i}. {title}", callback_data=f"music_select:{url}")])

            await msg.edit_text(
                "🎵 نتایج یافت شد، یکی را انتخاب کنید:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    except Exception as e:
        await msg.edit_text(f"❌ خطا در جستجوی موزیک:\n{e}")


# ------------------------------
# هندلر انتخاب آهنگ
# ------------------------------
async def music_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id

    if not query.data.startswith("music_select:"):
        return

    track_url = query.data.split(":", 1)[1]
    msg = await query.edit_message_text("⬇️ در حال دانلود آهنگ، لطفاً صبر کنید...")

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(track_url, download=True)
            filename = ydl.prepare_filename(info)

        mp3_path = await convert_to_mp3(filename)
        if mp3_path and os.path.exists(mp3_path):
            await context.bot.send_audio(chat_id, mp3_path, caption=f"🎵 {info.get('title','SoundCloud')}")
            os.remove(mp3_path)
        else:
            await context.bot.send_document(chat_id, filename, caption=f"🎵 {info.get('title','SoundCloud')}")

        if os.path.exists(filename):
            os.remove(filename)

        await msg.delete()
    except Exception as e:
        await msg.edit_message_text(f"❌ خطا در دانلود موزیک:\n{e}")
