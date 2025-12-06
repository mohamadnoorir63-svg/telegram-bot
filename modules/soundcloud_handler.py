# modules/soundcloud_handler.py
import os
import shutil
import subprocess
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


async def convert_to_mp3(file_path: str) -> str:
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


async def soundcloud_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """جستجو در SoundCloud با ۱۰ نتیجه"""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    # فقط وقتی پیام با "آهنگ" شروع شد
    if not text.startswith("آهنگ "):
        return

    query = text.replace("آهنگ ", "", 1).strip()
    if not query:
        await update.message.reply_text("❌ لطفاً متن یا نام آهنگ را وارد کنید.")
        return

    msg = await update.message.reply_text("🔍 در حال جستجو در SoundCloud ...")

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            # scsearch10 = گرفتن ۱۰ نتیجه
            info = ydl.extract_info(f"scsearch10:{query}", download=False)

            if not info or "entries" not in info:
                await msg.edit_text("❌ هیچ نتیجه‌ای یافت نشد.")
                return

            entries = [e for e in info["entries"] if e]

            if not entries:
                await msg.edit_text("❌ نتیجه مناسب پیدا نشد.")
                return

            # ساخت دکمه‌ها
            buttons = []
            for i, track in enumerate(entries[:10]):
                title = track.get("title", "بدون نام")
                url = track.get("webpage_url")  # لینک مستقیم صحیح
                buttons.append([
                    InlineKeyboardButton(text=f"{i+1} - {title[:40]}", callback_data=f"scdl:{url}")
                ])

            keyboard = InlineKeyboardMarkup(buttons)
            await msg.edit_text("🎵 نتایج پیدا شد، یکی را انتخاب کنید:", reply_markup=keyboard)

    except Exception as e:
        await msg.edit_text(f"❌ خطا در جستجو:\n{e}")


async def music_select_handler(update, context: ContextTypes.DEFAULT_TYPE):
    """دانلود آهنگ بعد از کلیک دکمه"""
    query = update.callback_query
    await query.answer()

    track_url = query.data.replace("scdl:", "")
    msg = await query.edit_message_text("⬇️ در حال دانلود... لطفا صبر کنید.")

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s")
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(track_url, download=True)
            filename = ydl.prepare_filename(info)

        mp3_path = await convert_to_mp3(filename)

        chat_id = query.message.chat_id

        if mp3_path and os.path.exists(mp3_path):
            await context.bot.send_audio(chat_id, mp3_path, caption=f"🎵 {info.get('title','SoundCloud')}")
            os.remove(mp3_path)
        else:
            await context.bot.send_document(chat_id, filename, caption=f"🎵 {info.get('title','SoundCloud')}")

        if os.path.exists(filename):
            os.remove(filename)

        await msg.delete()

    except Exception as e:
        await query.edit_message_text(f"❌ خطا در دانلود:\n{e}")
