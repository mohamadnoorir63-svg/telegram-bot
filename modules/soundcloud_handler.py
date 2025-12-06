# modules/soundcloud_handler.py
import os
import shutil
import subprocess
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# ذخیره نتایج جستجو (track_id -> info)
track_store = {}

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
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    chat_id = update.effective_chat.id
    text_l = text.lower()

    # -----------------------------
    # دستورات سه‌زبانه
    # -----------------------------
    triggers = [
        "آهنگ ",
        "music ",
        "اغنيه ",
        "أغنية ",
    ]

    used_trigger = None
    for t in triggers:
        if text_l.startswith(t):
            used_trigger = t
            break

    if not used_trigger:
        return

    query = text[len(used_trigger):].strip()
    if not query:
        await update.message.reply_text("❌ لطفاً نام یا متن آهنگ را وارد کنید.")
        return

    msg = await update.message.reply_text(f"🔍 در حال جستجو در SoundCloud ...")

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"scsearch10:{query}", download=False)

            if not info or "entries" not in info or not info["entries"]:
                await msg.edit_text("❌ آهنگ پیدا نشد.")
                return

            track_store[chat_id] = info["entries"]

            keyboard = []
            for track in info["entries"]:
                track_id = track.get("id")
                title = track.get("title", "SoundCloud Track")
                keyboard.append([InlineKeyboardButton(title, callback_data=f"music_select:{track_id}")])

            reply_markup = InlineKeyboardMarkup(keyboard)
            await msg.edit_text(f"🎵 {len(info['entries'])} آهنگ پیدا شد. لطفا انتخاب کنید:", reply_markup=reply_markup)

    except Exception as e:
        await msg.edit_text(f"❌ خطا در جستجوی موزیک:\n{e}")


async def music_select_handler(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    track_id = query.data.split(":")[1]
    chat_id = query.message.chat_id

    track_info = None
    for track in track_store.get(chat_id, []):
        if str(track.get("id")) == str(track_id):
            track_info = track
            break

    if not track_info:
        await query.edit_message_text("❌ خطا: آهنگ پیدا نشد.")
        return

    msg = await query.edit_message_text("⬇️ در حال دانلود آهنگ... لطفا صبر کنید.")

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(track_info["webpage_url"], download=True)
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
        await query.edit_message_text(f"❌ خطا در دانلود موزیک:\n{e}")
