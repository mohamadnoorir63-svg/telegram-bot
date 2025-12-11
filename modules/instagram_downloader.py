# modules/instagram_downloader.py

import os
import shutil
import subprocess
import asyncio
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Chat
from telegram.ext import ContextTypes

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

INSTAGRAM_COOKIES = """\
# Netscape HTTP Cookie File
.instagram.com  TRUE  /  TRUE  1799974131  csrftoken  --d8oLwWArIVOTuxrKibqa
.instagram.com  TRUE  /  TRUE  1799687399  datr  47Q1aZceuWl7nLkf_Uzh_kVW
.instagram.com  TRUE  /  TRUE  1796663399  ig_did  615B02DC-3964-40ED-864D-5EDD6E7C4EA3
.instagram.com  TRUE  /  TRUE  1799687399  mid  aTW04wABAAHoKpxsaAJbAfLsgVU3
.instagram.com  TRUE  /  TRUE  1765732343  dpr  2
.instagram.com  TRUE  /  TRUE  1773190131  ds_user_id  79160628834
.instagram.com  TRUE  /  TRUE  1766018928  wd  360x683
.instagram.com  TRUE  /  TRUE  1796933591  sessionid 79160628834%3AtMYF1zDBj9tXx3%3A7%3AAYjlXAe8pz6DF9H0JRMzmLpz4PmyQSRhYqRixrTn5w
.instagram.com  TRUE  /  TRUE  0  rur  "CLN\05479160628834\0541796950131:01fed2aade586e74cf94cfdcf02e9379c728a311e957c784caaee1ea3b4fedca58ea662c"
"""

# کش برای نگهداری مسیر فایل‌ها برای callback
video_store = {}

# ================================
# بررسی مدیر بودن
# ================================
async def is_admin(update, context):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == Chat.PRIVATE:
        return True
    try:
        admins = await context.bot.get_chat_administrators(chat.id)
        admin_ids = [a.user.id for a in admins]
        return user.id in admin_ids
    except:
        return False

# ================================
# تبدیل به mp3 بلوک‌کننده
# ================================
def _convert_to_mp3_blocking(video_path: str) -> str:
    mp3_path = video_path.rsplit(".", 1)[0] + ".mp3"
    if not shutil.which("ffmpeg"):
        return None
    subprocess.run(
        ["ffmpeg", "-y", "-i", video_path, "-vn", "-ab", "192k", "-ar", "44100", mp3_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return mp3_path

# ================================
# دانلود و پردازش ویدیو (blocking)
# ================================
def _download_instagram_blocking(url: str):
    cookie_path = os.path.join(DOWNLOAD_FOLDER, "instagram_cookie.txt")
    with open(cookie_path, "w", encoding="utf-8") as f:
        f.write(INSTAGRAM_COOKIES.strip())

    ydl_opts = {
        "format": "mp4",
        "quiet": True,
        "merge_output_format": "mp4",
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
        "cookiefile": cookie_path,
        "noplaylist": False,
        "ignoreerrors": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if not info:
            return None, None
        entries = info.get("entries", [info])
        filenames = []
        for entry in entries:
            filenames.append(ydl.prepare_filename(entry))
        return info, filenames

# ================================
# هندلر اصلی اینستاگرام
# ================================
async def instagram_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    url = update.message.text.strip()
    chat = update.effective_chat
    user = update.effective_user

    # محدود کردن گروه به مدیران
    if chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        allowed = await is_admin(update, context)
        if not allowed:
            return

    if "instagram.com" not in url:
        return

    msg = await update.message.reply_text("⬇️ در حال دانلود از Instagram ...")
    chat_id = chat.id

    try:
        loop = asyncio.get_running_loop()
        info, filenames = await loop.run_in_executor(None, _download_instagram_blocking, url)
        if not info or not filenames:
            await msg.edit_text("❌ امکان دانلود این پست وجود ندارد.")
            return

        # پردازش فایل‌ها
        for filename in filenames:
            if not os.path.exists(filename):
                continue
            video_id = os.path.basename(filename)

            video_store[video_id] = filename

            # دکمه‌ها
            keyboard = []
            if chat.type == Chat.PRIVATE:
                keyboard.append([
                    InlineKeyboardButton(
                        "➕ افزودن به گروه",
                        url="https://t.me/AFGR63_bot?startgroup=true"
                    )
                ])
            keyboard.append([
                InlineKeyboardButton(
                    "📥 دانلود صوتی",
                    callback_data=f"instagram_audio:{video_id}"
                )
            ])

            await context.bot.send_video(
                chat_id,
                filename,
                caption=f"🎬 {info.get('title', 'Instagram Video')}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود: {e}")

# ================================
# هندلر دانلود صوتی
# ================================
async def instagram_audio_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()

    video_id = cq.data.split(":")[1]
    if video_id not in video_store:
        return await cq.edit_message_text("❌ فایل ویدیو پیدا نشد.")

    video_path = video_store[video_id]

    loop = asyncio.get_running_loop()
    mp3_path = await loop.run_in_executor(None, _convert_to_mp3_blocking, video_path)

    if not mp3_path or not os.path.exists(mp3_path):
        return await cq.edit_message_text("❌ تبدیل به صوت ممکن نیست.")

    try:
        await context.bot.send_audio(
        cq.message.chat_id,
        mp3_path,
        caption="🎵 نسخه صوتی اینستاگرام"
    )
    except Exception as e:
        await cq.edit_message_text(f"❌ خطا در ارسال صوت: {e}")
    finally:
        if os.path.exists(mp3_path):
            os.remove(mp3_path)
