import os
import re
import yt_dlp
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# ================================
SUDO_USERS = [8588347189]  # آیدی شما
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# مسیر فایل کوکی واقعی
COOKIE_FILE = "insta_cookie.txt"

# ================================
# regex گرفتن لینک
URL_RE = re.compile(r"(https?://[^\s]+)")

# ================================
# دکمه افزودن ربات
ADD_BTN = InlineKeyboardMarkup([
    [InlineKeyboardButton("➕ افزودن ربات به گروه", url="https://t.me/AFGR63_bot?startgroup=true")]
])

# ================================
# چک مدیر بودن
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
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            await msg.edit_text("⬇ در حال ارسال فایل‌ها...")

            # چند پست یا آلبوم
            if "entries" in info:
                for entry in info["entries"]:
                    file = ydl.prepare_filename(entry)
                    ext = file.split(".")[-1].lower()
                    if ext in ["mp4", "mov", "webm"]:
                        await update.message.reply_video(video=open(file, "rb"),
                                                        caption=entry.get("title", ""),
                                                        reply_markup=ADD_BTN)
                    else:
                        await update.message.reply_photo(photo=open(file, "rb"),
                                                        caption=entry.get("title", ""),
                                                        reply_markup=ADD_BTN)
                await msg.delete()
                return

            # تک پست
            file = ydl.prepare_filename(info)
            ext = file.split(".")[-1].lower()
            if ext in ["mp4", "mov", "webm"]:
                await update.message.reply_video(video=open(file, "rb"),
                                                caption=info.get("title", ""),
                                                reply_markup=ADD_BTN)
            else:
                await update.message.reply_photo(photo=open(file, "rb"),
                                                caption=info.get("title", ""),
                                                reply_markup=ADD_BTN)

            # همزمان صوت هم می‌سازد
            audio_file = file.rsplit(".", 1)[0] + ".mp3"
            ydl_audio_opts = {
                "quiet": True,
                "cookiefile": COOKIE_FILE,
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192"
                }],
                "outtmpl": audio_file
            }
            with yt_dlp.YoutubeDL(ydl_audio_opts) as ydl2:
                ydl2.extract_info(url, download=True)
            await update.message.reply_audio(audio=open(audio_file, "rb"),
                                             caption=info.get("title", ""),
                                             reply_markup=ADD_BTN)

            await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ نتوانستم دانلود کنم.\n⚠️ خطا: {e}")
