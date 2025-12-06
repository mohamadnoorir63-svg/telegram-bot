# modules/soundcloud_handler.py
import os
import shutil
import subprocess
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# حافظه موقت برای نگهداری URL آهنگ‌ها
track_store = {}  # track_id -> url

async def convert_to_mp3(file_path: str) -> str:
    """تبدیل ویدیو/آهنگ به MP3"""
    mp3_path = file_path.rsplit(".", 1)[0] + ".mp3"
    if not shutil.which("ffmpeg"):
        return None
    cmd = [
        "ffmpeg", "-y", "-i", file_path,
        "-vn", "-ab", "192k", "-ar", "44100",
        "-f", "mp3", mp3_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return mp3_path

# =================== جستجو و نمایش دکمه ===================
async def soundcloud_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    chat_id = update.effective_chat.id

    # فقط وقتی متن با "آهنگ " شروع شد
    if not text.lower().startswith("آهنگ "):
        return

    query = text.replace("آهنگ ", "", 1).strip()
    if not query:
        await update.message.reply_text("❌ لطفاً نام یا متن آهنگ را وارد کنید.")
        return

    msg = await update.message.reply_text("🔍 در حال جستجو در SoundCloud ...")

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # جستجو
            info = ydl.extract_info(f"scsearch5:{query}", download=False)

            if not info or "entries" not in info or not info["entries"]:
                await msg.edit_text("❌ آهنگ پیدا نشد.")
                return

            # دکمه‌ها با شناسه کوتاه
            buttons = []
            for i, track in enumerate(info["entries"], start=1):
                title = track.get("title", "SoundCloud Track")
                url = track.get("webpage_url")
                track_id = f"sc{i}"
                track_store[track_id] = url
                buttons.append([InlineKeyboardButton(title, callback_data=f"music_select:{track_id}")])

            keyboard = InlineKeyboardMarkup(buttons)
            await msg.edit_text(f"🎵 نتیجه‌های پیدا شده برای: {query}", reply_markup=keyboard)

    except Exception as e:
        await msg.edit_text(f"❌ خطا در جستجوی موزیک:\n{e}")

# =================== دانلود با کلیک روی دکمه ===================
async def music_select_handler(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    track_id = query.data.split(":", 1)[1]

    track_url = track_store.get(track_id)
    if not track_url:
        await query.edit_message_text("❌ خطا: آهنگ یافت نشد!")
        return

    msg = await query.edit_message_text("⬇️ در حال دانلود آهنگ... لطفا صبر کنید.")

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(track_url, download=True)
            filename = ydl.prepare_filename(info)

        mp3_path = await convert_to_mp3(filename)
        if mp3_path and os.path.exists(mp3_path):
            await context.bot.send_audio(query.message.chat_id, mp3_path, caption=f"🎵 {info.get('title','SoundCloud')}")
            os.remove(mp3_path)
        else:
            await context.bot.send_document(query.message.chat_id, filename, caption=f"🎵 {info.get('title','SoundCloud')}")

        if os.path.exists(filename):
            os.remove(filename)

        await msg.delete()
    except Exception as e:
        await query.edit_message_text(f"❌ خطا در دانلود آهنگ:\n{e}")
