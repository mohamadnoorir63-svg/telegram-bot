import os
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
import yt_dlp
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# ================================
# سودو
# ================================
SUDO_USERS = [8588347189]  # آیدی شما

# ================================
# کوکی اینستاگرام
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
with open(COOKIE_FILE, "w", encoding="utf-8") as f:
    f.write(INSTAGRAM_COOKIES.strip())

# ================================
# مسیر دانلود و regex
# ================================
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
URL_RE = re.compile(r"(https?://[^\s]+)")
executor = ThreadPoolExecutor(max_workers=3)

# ================================
# دکمه افزودن ربات
# ================================
def get_add_btn(chat_type):
    if chat_type == "private":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ افزودن ربات به گروه", url="https://t.me/AFGR63_bot?startgroup=true")]
        ])
    return None

# ================================
# چک مدیر بودن
# ================================
async def is_admin(update, context):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private":
        return True
    if user.id in SUDO_USERS:
        return True
    try:
        admins = await context.bot.get_chat_administrators(chat.id)
        return user.id in [a.user.id for a in admins]
    except:
        return False

# ================================
# هندلر اصلی اینستاگرام
# ================================
async def instagram_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    m = URL_RE.search(text)
    if not m:
        return
    url = m.group(1)
    if "instagram.com" not in url:
        return

    # محدودیت در گروه
    if update.effective_chat.type != "private":
        allowed = await is_admin(update, context)
        if not allowed:
            return

    msg = await update.message.reply_text("📥 در حال بررسی لینک اینستاگرام...")

    ydl_opts = {
        "quiet": True,
        "cookiefile": COOKIE_FILE,
        "format": "bestvideo+bestaudio/best",  # دانلود همزمان ویدیو و صوت
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
        "merge_output_format": "mp4",
    }

    try:
        loop = asyncio.get_running_loop()
        info = await loop.run_in_executor(executor, lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(url, download=True))
        files = []

        # بررسی تک پست یا چندتایی
        entries = info.get("entries", [info])
        for entry in entries:
            file_path = yt_dlp.YoutubeDL(ydl_opts).prepare_filename(entry)
            if not os.path.exists(file_path):
                await msg.edit_text(f"❌ فایل پیدا نشد: {file_path}")
                continue

            ext = file_path.split(".")[-1].lower()
            if ext in ["mp4", "mov", "webm"]:
                await update.message.reply_video(video=open(file_path, "rb"), caption=entry.get("title",""))
            elif ext in ["jpg", "jpeg", "png", "webp"]:
                await update.message.reply_photo(photo=open(file_path, "rb"), caption=entry.get("title",""))
            
            # تولید فایل صوتی MP3 از ویدیو
            audio_file = file_path.rsplit(".", 1)[0] + ".mp3"
            if not os.path.exists(audio_file):
                ydl_audio_opts = {
                    "quiet": True,
                    "cookiefile": COOKIE_FILE,
                    "format": "bestaudio/best",
                    "postprocessors": [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }],
                    "outtmpl": audio_file,
                }
                await loop.run_in_executor(executor, lambda: yt_dlp.YoutubeDL(ydl_audio_opts).extract_info(url, download=True))

            if os.path.exists(audio_file):
                await update.message.reply_audio(audio=open(audio_file,"rb"), caption=entry.get("title",""))

        await msg.delete()
        # دکمه افزودن ربات در پیوی
        if update.effective_chat.type == "private":
            await update.message.reply_text("➕ افزودن ربات به گروه:", reply_markup=get_add_btn(update.effective_chat.type))

    except Exception as e:
        await msg.edit_text(f"❌ نتوانستم دانلود کنم.\n⚠️ خطا: {e}")
