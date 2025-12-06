# ================== شروع بخش TikTok Downloader ==================

import os
import requests
import subprocess
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from yt_dlp import YoutubeDL
from bs4 import BeautifulSoup

# پوشه ذخیره‌سازی
os.makedirs("downloads", exist_ok=True)

# تبدیل فایل ویدیو به mp3
def convert_to_mp3(video_path):
    mp3_path = video_path.rsplit(".", 1)[0] + ".mp3"
    command = [
        "ffmpeg",
        "-y",  # overwrite if exists
        "-i", video_path,
        "-vn",  # بدون ویدیو
        "-ab", "192k",
        "-ar", "44100",
        "-f", "mp3",
        mp3_path
    ]
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return mp3_path

# استخراج لینک عکس TikTok از HTML
def get_tiktok_photo(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        meta = soup.find("meta", property="og:image")
        if meta:
            return meta["content"]
    except:
        return None
    return None

# هندلر دانلود TikTok
async def tiktok_downloader(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    chat_id = update.effective_chat.id

    msg = await update.message.reply_text("⬇️ در حال پردازش رسانه TikTok ...")

    # ریدایرکت لینک کوتاه TikTok
    if "vm.tiktok.com" in url or "vt.tiktok.com" in url:
        try:
            resp = requests.get(url, allow_redirects=True, timeout=10)
            url = resp.url
        except Exception as e:
            await msg.edit_text(f"❌ خطا در ریدایرکت لینک TikTok: {e}")
            return

    # عکس TikTok
    if "/photo/" in url:
        photo_url = get_tiktok_photo(url)
        if not photo_url:
            await msg.edit_text("❌ خطا در دانلود عکس TikTok: لینک معتبر پیدا نشد")
            return
        try:
            filename = f"downloads/{photo_url.split('/')[-1].split('?')[0]}"
            r = requests.get(photo_url)
            with open(filename, "wb") as f:
                f.write(r.content)
            await context.bot.send_photo(chat_id, photo=open(filename, "rb"), caption="🖼 عکس TikTok")
            os.remove(filename)
            await msg.delete()
        except Exception as e:
            await msg.edit_text(f"❌ خطا در دانلود عکس TikTok: {e}")
        return

    # دانلود ویدیو TikTok
    ydl_opts = {
        "format": "mp4",
        "outtmpl": "downloads/%(id)s.%(ext)s",
        "quiet": True,
        "noplaylist": True,
        "merge_output_format": "mp4"
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        # ارسال ویدیو
        await context.bot.send_video(chat_id, video=open(filename, "rb"), caption=f"🎬 {info.get('title','TikTok Video')}")

        # استخراج و ارسال صوت mp3 همزمان
        mp3_path = convert_to_mp3(filename)
        await context.bot.send_audio(chat_id, audio=open(mp3_path, "rb"), caption="🎵 صوت ویدیو")

        # پاکسازی فایل‌ها
        os.remove(filename)
        os.remove(mp3_path)
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود ویدیو/صوت: {e}")
        print(e)

# ================== پایان بخش TikTok Downloader ==================

# ثبت هندلر در ربات اصلی:
# application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"https?://(www\.)?(tiktok\.com|vm\.tiktok\.com|vt\.tiktok\.com)/"), tiktok_downloader))
