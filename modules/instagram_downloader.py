# modules/instagram_handler.py
import os
import shutil
import subprocess
import asyncio
import yt_dlp
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

INSTAGRAM_COOKIES = """\
# Netscape HTTP Cookie File
.instagram.com	TRUE	/	TRUE	1799974131	csrftoken	--d8oLwWArIVOTuxrKibqa
.instagram.com	TRUE	/	TRUE	1799687399	datr	47Q1aZceuWl7nLkf_Uzh_kVW
.instagram.com	TRUE	/	TRUE	1796663399	ig_did	615B02DC-3964-40ED-864D-5EDD6E7C4EA3
.instagram.com	TRUE	/	TRUE	1799687399	mid	aTW04wABAAHoKpxsaAJbAfLsgVU3
.instagram.com	TRUE	/	TRUE	1765732343	dpr	2
.instagram.com	TRUE	/	TRUE	1773190131	ds_user_id	79160628834
.instagram.com	TRUE	/	TRUE	1766018928	wd	360x683
.instagram.com	TRUE	/	TRUE	1796933591	sessionid	79160628834%3AtMYF1zDBj9tXx3%3A7%3AAYjlXAe8pz6DF9H0JRMzmLpz4PmyQSRhYqRixrTn5w
.instagram.com	TRUE	/	TRUE	0	rur	"CLN\05479160628834\0541796950131:01fed2aade586e74cf94cfdcf02e9379c728a311e957c784caaee1ea3b4fedca58ea662c"
"""

async def convert_to_mp3_bytes(video_path: str) -> BytesIO:
    """تبدیل ویدیو به MP3 و بازگشت BytesIO"""
    if not shutil.which("ffmpeg"):
        return None

    mp3_data = BytesIO()

    def ffmpeg_run():
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path,
            "-vn", "-ab", "192k", "-ar", "44100",
            "-f", "mp3", "pipe:1"
        ], stdout=mp3_data, stderr=subprocess.DEVNULL)

    await asyncio.to_thread(ffmpeg_run)
    mp3_data.seek(0)
    return mp3_data if mp3_data.getbuffer().nbytes > 0 else None

async def instagram_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    url = update.message.text.strip()
    chat_id = update.effective_chat.id

    if "instagram.com" not in url:
        return

    msg = await update.message.reply_text("⬇️ در حال دانلود از Instagram ...")

    cookie_path = os.path.join(DOWNLOAD_FOLDER, "instagram_cookie.txt")
    with open(cookie_path, "w", encoding="utf-8") as f:
        f.write(INSTAGRAM_COOKIES.strip())

    ydl_opts = {
        "format": "mp4",
        "quiet": True,
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
        "merge_output_format": "mp4",
        "cookiefile": cookie_path,
        "noplaylist": False,
        "ignoreerrors": True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info is None:
                await msg.edit_text("❌ امکان دانلود این پست وجود ندارد.")
                return

            entries = info.get("entries", [info])

            for entry in entries:
                filename = ydl.prepare_filename(entry)
                if not os.path.exists(filename):
                    continue

                # دکمه‌ها
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎵 دانلود صوتی", callback_data=f"audio_inline|{filename}")],
                    [InlineKeyboardButton("➕ افزودن به گروه", url="https://t.me/AFGR63_bot?startgroup=true")]
                ])

                # ارسال ویدیو با دکمه‌ها
                with open(filename, "rb") as fvideo:
                    await context.bot.send_video(
                        chat_id, fvideo,
                        caption=f"🎬 {entry.get('title', 'Instagram Video')}",
                        reply_markup=keyboard
                    )

        os.remove(cookie_path)
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود از اینستاگرام: {e}")

async def audio_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.data:
        return

    data = query.data
    if not data.startswith("audio_inline|"):
        return

    video_path = data.split("|", 1)[1]

    if not os.path.exists(video_path):
        await query.answer("❌ فایل ویدیو دیگر موجود نیست.")
        return

    mp3_data = await convert_to_mp3_bytes(video_path)
    if not mp3_data:
        await query.answer("❌ خطا در تبدیل صوتی.")
        return

    await context.bot.send_audio(query.message.chat_id, mp3_data, caption="🎵 صوت ویدیو")
    await query.answer("✅ صوت ارسال شد.")
