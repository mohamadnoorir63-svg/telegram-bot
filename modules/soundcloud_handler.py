# modules/soundcloud_handler.py
import os
import shutil
import subprocess
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# -------------------------------
# تبدیل به MP3
# -------------------------------
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

# -------------------------------
# هندلر جستجو و ارسال آهنگ
# -------------------------------
async def soundcloud_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    chat_id = update.effective_chat.id

    # استفاده از ۵ کلمه اول متن به عنوان کلیدواژه
    words = text.split()
    if not words:
        await update.message.reply_text("❌ لطفاً نام یا متن آهنگ را وارد کنید.")
        return

    search_query = " ".join(words[:5])

    msg = await update.message.reply_text(f"🔍 در حال جستجو در SoundCloud با کلیدواژه:\n`{search_query}`", parse_mode="Markdown")

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"scsearch5:{search_query}", download=False)

            if not info or "entries" not in info or not info["entries"]:
                await msg.edit_text("❌ آهنگ پیدا نشد.")
                return

            # ایجاد دکمه‌ها برای انتخاب ۵ نتیجه اول
            buttons = []
            for i, track in enumerate(info["entries"][:5], start=1):
                title = track.get("title", "SoundCloud Track")
                track_id = track.get("id")
                buttons.append([InlineKeyboardButton(f"{i}. {title}", callback_data=f"music_select:{track_id}")])

            keyboard = InlineKeyboardMarkup(buttons)
            await msg.edit_text("🎵 چند نتیجه پیدا شد. لطفا یکی را انتخاب کنید:", reply_markup=keyboard)

    except Exception as e:
        await msg.edit_text(f"❌ خطا در جستجوی موزیک:\n{e}")


# -------------------------------
# هندلر انتخاب آهنگ
# -------------------------------
async def music_select_handler(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    track_id = query.data.split(":")[1]

    msg = await query.edit_message_text("⬇️ در حال دانلود آهنگ... لطفا صبر کنید.")

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://soundcloud.com/i/tracks/{track_id}", download=True)
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
        await msg.edit_message_text(f"❌ خطا در دانلود آهنگ:\n{e}")
