import re
import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes

# ================================
#   📌 کوکی‌های اینستاگرام (داخل کد)
# ================================
INSTAGRAM_COOKIES = """
# Netscape HTTP Cookie File
.instagram.com	TRUE	/	TRUE	1799701606	csrftoken	--d8oLwWArIVOTuxrKibqa
.instagram.com	TRUE	/	TRUE	1799687399	datr	47Q1aZceuWl7nLkf_Uzh_kVW
.instagram.com	TRUE	/	TRUE	1796663399	ig_did	615B02DC-3964-40ED-864D-5EDD6E7C4EA3
.instagram.com	TRUE	/	TRUE	1799687399	mid	aTW04wABAAHoKpxsaAJbAfLsgVU3
.instagram.com	TRUE	/	TRUE	1765732343	dpr	2
.instagram.com	TRUE	/	TRUE	1772917606	ds_user_id	79160628834
.instagram.com	TRUE	/	TRUE	1796663585	sessionid	79160628834%3AtMYF1zDBj9tXx3%3A7%3AAYhX_MD6k4rrVPUaIBvVhJLqxdAzNqJ0SkLDHb-ymQ
.instagram.com	TRUE	/	TRUE	1765746400	wd	360x683
.instagram.com	TRUE	/	TRUE	0	rur	"FRC\05479160628834\0541796677606:01feeadcb720f15c682519c2475d06626b55e5e1646ce3648355ab004152c377c46ba081"
"""

COOKIE_FILE = "insta_cookie.txt"

# ذخیره فایل کوکی در زمان اجرا
with open(COOKIE_FILE, "w") as f:
    f.write(INSTAGRAM_COOKIES.strip())


# استخراج URL
URL_RE = re.compile(r"(https?://[^\s]+)")


async def instagram_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    m = URL_RE.search(text)

    if not m:
        return

    url = m.group(1)

    if "instagram.com" not in url:
        return

    msg = await update.message.reply_text("📥 در حال بررسی لینک اینستاگرام...")

    # yt-dlp تنظیمات
    ydl_opts = {
        "quiet": True,
        "cookiefile": COOKIE_FILE,
        "format": "bestvideo+bestaudio/best",   # ← دریافت ویدیو + صوت
        "outtmpl": "downloads/%(id)s.%(ext)s",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        await msg.edit_text("⬇ در حال ارسال فایل‌ها...")

        # ارسال ویدیو (اگر ویدیو بود)
        if filename.endswith((".mp4", ".mkv", ".webm")):
            await update.message.reply_video(
                video=open(filename, "rb"),
                caption="🎬 ویدیو با موفقیت دانلود شد!"
            )

        # ارسال صوت جداگانه (اگر ترک صوتی وجود داشت)
        if "audio" in info.get("formats", [{}])[0].get("format_note", "").lower():
            audio_path = filename.rsplit(".", 1)[0] + ".mp3"
            await update.message.reply_audio(
                audio=open(audio_path, "rb"),
                caption="🎵 فایل صوتی جداگانه"
            )

    except Exception as e:
        await msg.edit_text(f"❌ نتوانستم دانلود کنم.\n⚠️ خطا: {e}")
