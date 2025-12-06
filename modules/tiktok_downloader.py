# ================== TikTok Downloader برای ربات اصلی ==================
import os
import requests
import subprocess
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

import yt_dlp

# پوشه دانلود
os.makedirs("downloads", exist_ok=True)

# مسیر ffmpeg را پیدا کن
def find_ffmpeg():
    for cmd in ["ffmpeg", "/app/.heroku/bin/ffmpeg", "/app/.apt/usr/bin/ffmpeg"]:
        if subprocess.run([cmd, "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
            return cmd
    return None

FFMPEG_PATH = find_ffmpeg()
if not FFMPEG_PATH:
    print("⚠️ ffmpeg پیدا نشد! صوت ویدیوها فرستاده نمی‌شود.")

# تبدیل ویدیو به mp3
def convert_to_mp3(video_path):
    mp3_path = video_path.rsplit(".", 1)[0] + ".mp3"
    if not FFMPEG_PATH or not os.path.exists(video_path):
        return None
    subprocess.run([
        FFMPEG_PATH, "-y", "-i", video_path,
        "-vn", "-ab", "192k", "-ar", "44100", "-f", "mp3", mp3_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return mp3_path if os.path.exists(mp3_path) else None

# هندلر TikTok
async def tiktok_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    msg = await update.message.reply_text("⬇️ در حال پردازش رسانه TikTok ...")

    # ریدایرکت لینک کوتاه TikTok
    if "vm.tiktok.com" in url or "vt.tiktok.com" in url:
        try:
            resp = requests.get(url, allow_redirects=True)
            url = resp.url
        except Exception as e:
            await msg.edit_text(f"❌ خطا در ریدایرکت لینک TikTok: {e}")
            return

    # عکس TikTok
    if "/photo/" in url:
        try:
            filename = f"downloads/{url.split('/')[-1]}.jpg"
            r = requests.get(url)
            with open(filename, "wb") as f:
                f.write(r.content)
            await context.bot.send_photo(update.effective_chat.id, filename, caption="🖼 عکس TikTok")
            os.remove(filename)
            await msg.delete()
        except Exception as e:
            await msg.edit_text(f"❌ خطا در دانلود عکس TikTok: {e}")
        return

    # دانلود ویدیو
    ydl_opts = {
        "format": "mp4",
        "outtmpl": "downloads/%(id)s.%(ext)s",
        "quiet": True,
        "noplaylist": True,
        "merge_output_format": "mp4"
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        if not os.path.exists(filename):
            await msg.edit_text("❌ فایل ویدیو دانلود نشد!")
            return

        # ارسال ویدیو
        await context.bot.send_video(update.effective_chat.id, filename, caption=f"🎬 {info.get('title', 'TikTok Video')}")

        # تبدیل و ارسال صوت
        mp3_path = convert_to_mp3(filename)
        if mp3_path:
            await context.bot.send_audio(update.effective_chat.id, mp3_path, caption="🎵 صوت ویدیو")
            os.remove(mp3_path)

        os.remove(filename)
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود ویدیو/صوت: {e}")
        print(e)

# تابع برای ثبت هندلر در ربات اصلی
def register_tiktok_handler(app):
    app.add_handler(MessageHandler(filters.Regex(r"https?://(www\.)?(tiktok\.com|vm\.tiktok\.com|vt\.tiktok\.com)/.+"), tiktok_handler))
