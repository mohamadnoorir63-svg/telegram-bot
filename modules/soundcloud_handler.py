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

    # اگر پیام آهنگ نبود → هیچ کاری نکن
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    # فقط وقتی متن با "آهنگ " شروع شود
    if not text.startswith("آهنگ "):
        return

    query_text = text.replace("آهنگ ", "", 1).strip()

    msg = await update.message.reply_text(
        f"🔍 در حال جستجو برای:\n`{query_text}`",
        parse_mode="Markdown"
    )

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(f"scsearch5:{query_text}", download=False)

            if not info or not info.get("entries"):
                await msg.edit_text("❌ آهنگ پیدا نشد.")
                return

            buttons = []
            for entry in info["entries"][:5]:
                title = entry.get("title", "Track")
                url = entry.get("url")
                buttons.append([
                    InlineKeyboardButton(title, callback_data=f"scdl:{url}")
                ])

            keyboard = InlineKeyboardMarkup(buttons)
            await msg.edit_text("🎵 لطفاً یک آهنگ را انتخاب کنید:", reply_markup=keyboard)

    except Exception as e:
        await msg.edit_text(f"❌ خطا:\n{e}")


async def soundcloud_download_callback(update, context):
    query = update.callback_query
    await query.answer()

    url = query.data.replace("scdl:", "")

    msg = await query.edit_message_text("⬇️ در حال دانلود آهنگ... لطفا صبر کنید.")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
        "quiet": True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        mp3 = await convert_to_mp3(filename)
        if mp3 and os.path.exists(mp3):
            await query.message.reply_audio(mp3, caption=f"🎵 {info['title']}")
            os.remove(mp3)
        else:
            await query.message.reply_document(filename, caption=f"🎵 {info['title']}")

        if os.path.exists(filename):
            os.remove(filename)

        await msg.delete()

    except Exception as e:
        await msg.edit_message_text(f"❌ خطا در دانلود:\n{e}")
