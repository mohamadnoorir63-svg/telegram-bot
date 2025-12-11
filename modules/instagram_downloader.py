# telegram-bot/modules/instagram_downloader.py

import os
import shutil
import subprocess
import asyncio
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Chat
from telegram.ext import ContextTypes

# ================================
# تنظیمات
# ================================
SUDO_USERS = [8588347189]  # ← آیدی شما
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

INSTAGRAM_COOKIES = """\
# Netscape HTTP Cookie File
.instagram.com	TRUE	/	TRUE	1799977780	csrftoken	--d8oLwWArIVOTuxrKibqa
.instagram.com	TRUE	/	TRUE	1799687399	datr	47Q1aZceuWl7nLkf_Uzh_kVW
.instagram.com	TRUE	/	TRUE	1796663399	ig_did	615B02DC-3964-40ED-864D-5EDD6E7C4EA3
.instagram.com	TRUE	/	TRUE	1799687399	mid	aTW04wABAAHoKpxsaAJbAfLsgVU3
.instagram.com	TRUE	/	TRUE	1765732343	dpr	2
.instagram.com	TRUE	/	TRUE	1773193780	ds_user_id	79160628834
.instagram.com	TRUE	/	TRUE	1766022576	wd	360x683
.instagram.com	TRUE	/	TRUE	1796933591	sessionid	79160628834%3AtMYF1zDBj9tXx3%3A7%3AAYjlXAe8pz6DF9H0JRMzmLpz4PmyQSRhYqRixrTn5w
.instagram.com	TRUE	/	TRUE	0	rur	"CLN\05479160628834\0541796953780:01fe354b018be3558f1977c6d5d2af3c4df7b30c01a2b6405fc52893b2c404d3d3e6a3ae"
"""

# ================================
# کش مسیر فایل‌ها
# ================================
video_store = {}

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
# چک مدیر بودن (گروه)
# ================================
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == Chat.PRIVATE:
        return True
    if user.id in SUDO_USERS:
        return True
    try:
        admins = await context.bot.get_chat_administrators(chat.id)
        admin_ids = [a.user.id for a in admins]
        return user.id in admin_ids
    except:
        return False

# ================================
# هندلر اصلی اینستاگرام
# ================================
async def instagram_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    chat = update.effective_chat
    user = update.effective_user
    chat_id = chat.id
    url = update.message.text.strip()

    if "instagram.com" not in url:
        return

    # چک دسترسی در گروه‌ها
    if chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        allowed = await is_admin(update, context)
        if not allowed:
            return  # سکوت برای کاربران عادی

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
            if not info:
                await msg.edit_text("❌ امکان دانلود این پست وجود ندارد.")
                return

            entries = info.get("entries", [info])
            for entry in entries:
                filename = ydl.prepare_filename(entry)
                if not os.path.exists(filename):
                    continue

                video_id = entry.get("id")
                video_store[video_id] = filename

                # دکمه‌ها
                keyboard = []

                # افزودن به گروه فقط در پیوی
                if chat.type == Chat.PRIVATE:
                    keyboard.append([
                        InlineKeyboardButton(
                            "➕ افزودن به گروه",
                            url="https://t.me/AFGR63_bot?startgroup=true"
                        )
                    ])

                # دانلود صوتی
                keyboard.append([
                    InlineKeyboardButton(
                        "🎵 دانلود صوتی",
                        callback_data=f"instagram_audio:{video_id}"
                    )
                ])

                # ارسال ویدیو با دکمه‌ها
                with open(filename, "rb") as fvideo:
                    await context.bot.send_video(
                        chat_id,
                        fvideo,
                        caption=f"🎬 {entry.get('title', 'Instagram Video')}",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )

        os.remove(cookie_path)
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود از اینستاگرام: {e}")

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
    mp3_path = video_path.rsplit('.',1)[0] + ".mp3"

    # تبدیل غیر بلوک‌کننده
    mp3_path = await convert_to_mp3(video_path)

    if not mp3_path or not os.path.exists(mp3_path):
        return await cq.edit_message_text("❌ تبدیل به صوت ممکن نیست.")

    try:
        with open(mp3_path, "rb") as faudio:
            await context.bot.send_audio(cq.message.chat_id, faudio, caption="🎵 نسخه صوتی ویدیو")
    except Exception as e:
        await cq.edit_message_text(f"❌ خطا در ارسال صوت: {e}")
    finally:
        if os.path.exists(mp3_path):
            os.remove(mp3_path)
