# modules/youtube_downloader.py
import os
import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes
import re

# ================================
# 📌 کوکی‌های یوتیوب داخل کد (از خودت)
# ================================
YOUTUBE_COOKIES = """
.youtube.com	TRUE	/	TRUE	1796681120	__Secure-1PSIDTS	sidts-CjUBflaCdQcOtbfDt-nRp2oFwMBpfscyZZMzEzZ6aJ1sLKd1IcwA5pmRFHD6glmEEpfV0YCuARAA
.youtube.com	TRUE	/	TRUE	1796681120	__Secure-3PSIDTS	sidts-CjUBflaCdQcOtbfDt-nRp2oFwMBpfscyZZMzEzZ6aJ1sLKd1IcwA5pmRFHD6glmEEpfV0YCuARAA
.youtube.com	TRUE	/	FALSE	1799705120	HSID	AjTGPu3s0ssOMGmdt
.youtube.com	TRUE	/	TRUE	1799705120	SSID	AoWSAlkTiFw-Dz-vx
.youtube.com	TRUE	/	FALSE	1799705120	APISID	HxvXQSYkXGNgYpof/AFT19W4Wez3p3UcIH
.youtube.com	TRUE	/	TRUE	1799705120	SAPISID	_rcraLOX-PKvwhu4/AF9NcPAxfy-kfJMFD
.youtube.com	TRUE	/	TRUE	1799705120	__Secure-1PAPISID	_rcraLOX-PKvwhu4/AF9NcPAxfy-kfJMFD
.youtube.com	TRUE	/	TRUE	1799705120	__Secure-3PAPISID	_rcraLOX-PKvwhu4/AF9NcPAxfy-kfJMFD
.youtube.com	TRUE	/	FALSE	1799705120	SID	g.a0004Qi6jym_HRITeYANcuvacvEX1n3U2f-12S7BODezxV102T6kO9WpabcF0iQ30aKxMecIPAACgYKATsSARUSFQHGX2MijUWJ-ZsvcGEkOR_AeAJs4hoVAUF8yKpEcRbtGGH1RWTfllFjA0LL0076
.youtube.com	TRUE	/	TRUE	1799705120	__Secure-1PSID	g.a0004Qi6jym_HRITeYANcuvacvEX1n3U2f-12S7BODezxV102T6kuenCZ93IQFHAlg5uLVgQmQACgYKAW8SARUSFQHGX2MiIQNKrQhBYpDgboHODYMFexoVAUF8yKotd0bxWtWYAAyyIEh4HcXo0076
.youtube.com	TRUE	/	TRUE	1799705120	__Secure-3PSID	g.a0004Qi6jym_HRITeYANcuvacvEX1n3U2f-12S7BODezxV102T6kFJyk7bFhNUN7bNDub2dfLgACgYKAQoSARUSFQHGX2Mi7FGyLoUu8qk9JF6vqv8bMBoVAUF8yKq_x7FJo417PItBJsFLw86X0076
"""

# ذخیره خودکار کوکی‌ها در فایل
COOKIE_FILE = "youtube_cookie.txt"
with open(COOKIE_FILE, "w") as f:
    f.write(YOUTUBE_COOKIES.strip())

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

URL_RE = re.compile(r"(https?://[^\s]+)")


async def youtube_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    match = URL_RE.search(text)
    if not match:
        return

    url = match.group(1)

    if "youtube.com" not in url and "youtu.be" not in url:
        return

    msg = await update.message.reply_text("📥 در حال پردازش لینک یوتیوب...")

    ydl_opts = {
        "cookiefile": COOKIE_FILE,             # ← استفاده از کوکی
        "quiet": True,
        "format": "best",
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
        "noplaylist": True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        title = info.get("title", "YouTube Video")

        # ارسال ویدیو
        await msg.edit_text("⬇ در حال ارسال فایل...")
        await update.message.reply_video(
            video=open(filename, "rb"),
            caption=f"📥 {title}"
        )

        # ارسال صوت MP3
        await update.message.reply_text("🎧 در حال استخراج نسخه صوتی...")

        mp3_file = filename.replace(".mp4", ".mp3")

        os.system(f'ffmpeg -i "{filename}" -vn -ab 192k "{mp3_file}" -y')

        await update.message.reply_audio(
            audio=open(mp3_file, "rb"),
            caption=f"🎵 {title}"
        )

        # پاکسازی
        os.remove(filename)
        os.remove(mp3_file)

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود یوتیوب:\n{e}")
