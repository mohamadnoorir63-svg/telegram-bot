from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Chat
from telegram.ext import ContextTypes
import os, shutil, subprocess, asyncio, yt_dlp

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
.instagram.com  TRUE  /  TRUE  1796933591  sessionid  79160628834%3AtMYF1zDBj9tXx3%3A7%3AAYjlXAe8pz6DF9H0JRMzmLpz4PmyQSRhYqRixrTn5w
.instagram.com  TRUE  /  TRUE  0  rur  "CLN\05479160628834\0541796950131:01fed2aade586e74cf94cfdcf02e9379c728a311e957c784caaee1ea3b4fedca58ea662c"
"""

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

async def instagram_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    chat = update.effective_chat
    user = update.effective_user
    chat_id = chat.id
    url = update.message.text.strip()

    # بررسی نوع چت
    if chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        admins = await context.bot.get_chat_administrators(chat_id)
        admin_ids = [admin.user.id for admin in admins]

        # اگر کاربر غیرمدیر لینک بفرستد → پیام حذف شود و ربات سکوت کند
        if user.id not in admin_ids:
            try:
                await update.message.delete()
            except:
                pass
            return

    # داخل پیوی همه می‌توانند استفاده کنند
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

    group_button = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ افزودن به گروه", url="https://t.me/AFGR63_bot?startgroup=true")]
    ])

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

                # ارسال ویدیو
                with open(filename, "rb") as fvideo:
                    await context.bot.send_video(
                        chat_id, fvideo,
                        caption=f"🎬 {entry.get('title', 'Instagram Video')}",
                        reply_markup=group_button
                    )

                # ارسال صوت
                mp3_path = await convert_to_mp3(filename)
                if mp3_path and os.path.exists(mp3_path):
                    with open(mp3_path, "rb") as faudio:
                        await context.bot.send_audio(
                            chat_id, faudio,
                            caption="🎵 صوت ویدیو",
                            reply_markup=group_button
                        )
                    os.remove(mp3_path)

                os.remove(filename)

        os.remove(cookie_path)
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود از اینستاگرام: {e}")
