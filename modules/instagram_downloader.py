# modules/instagram_handler.py
import os
import shutil
import subprocess
import asyncio
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# ================================
# کوکی اینستاگرام درون‌خطی (Netscape format)
# ================================
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

# ================================
# تبدیل ویدیو به MP3 غیر بلوک‌کننده
# ================================
async def convert_to_mp3(video_path: str) -> str:
    mp3_path = video_path.rsplit(".", 1)[0] + ".mp3"
    if not shutil.which("ffmpeg"):
        return None

    def ffmpeg_run():
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path,
            "-vn", "-ab", "192k", "-ar", "44100",
            "-f", "mp3", mp3_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    await asyncio.to_thread(ffmpeg_run)
    return mp3_path if os.path.exists(mp3_path) else None

# ================================
# هندلر اصلی اینستاگرام
# ================================
async def instagram_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    url = update.message.text.strip()
    chat_id = update.effective_chat.id

    if "instagram.com" not in url:
        await update.message.reply_text("❌ این لینک معتبر نیست.")
        return

    msg = await update.message.reply_text("⬇️ در حال دانلود از Instagram ...")

    # فایل کوکی موقت بساز
    cookie_path = os.path.join(DOWNLOAD_FOLDER, "instagram_cookie.txt")
    with open(cookie_path, "w", encoding="utf-8") as f:
        f.write(INSTAGRAM_COOKIES.strip())

    ydl_opts = {
        "format": "bestvideo+bestaudio/best",
        "quiet": True,
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
        "merge_output_format": "mp4",
        "cookiefile": cookie_path,
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

                buttons = [
                    [
                        InlineKeyboardButton("🎵 دانلود صوت", callback_data=f"audio|{filename}"),
                        InlineKeyboardButton("➕ افزودن به گروه", url=f"https://t.me/AFGR63_bot?startgroup=true")
                    ]
                ]
                markup = InlineKeyboardMarkup(buttons)

                if entry.get("ext") == "jpg" or entry.get("is_image", False):
                    # ارسال عکس
                    await context.bot.send_photo(chat_id, open(filename, "rb"), caption="🖼 عکس اینستاگرام", reply_markup=markup)
                else:
                    # ارسال ویدیو
                    await context.bot.send_video(chat_id, open(filename, "rb"), caption=f"🎬 {entry.get('title', 'Instagram Video')}", reply_markup=markup)

                os.remove(filename)

        os.remove(cookie_path)
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود از اینستاگرام: {e}")


# ================================
# هندلر دکمه دانلود صوت
# ================================
async def instagram_audio_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.data:
        return

    data = query.data
    if not data.startswith("audio|"):
        return

    video_path = data.split("|")[1]

    await query.answer("🎵 در حال ساخت صوت ...", show_alert=False)

    if not os.path.exists(video_path):
        await query.edit_message_text("❌ فایل ویدیو پیدا نشد.")
        return

    mp3_path = await convert_to_mp3(video_path)
    if mp3_path:
        await context.bot.send_audio(query.message.chat.id, open(mp3_path, "rb"), caption="🎵 صوت ویدیو")
        os.remove(mp3_path)
    else:
        await query.edit_message_text("❌ خطا در ساخت صوت.")
