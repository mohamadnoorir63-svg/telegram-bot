# modules/instagram_handler_buttons.py
import asyncio
import yt_dlp
import subprocess
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

# کوکی اینستاگرام درون‌خطی
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

# ===================================================
# تبدیل ویدیو BytesIO به MP3 BytesIO
# ===================================================
async def convert_to_mp3_bytes(video_bytes: BytesIO) -> BytesIO:
    mp3_bytes = BytesIO()
    video_bytes.seek(0)
    video_temp = BytesIO(video_bytes.read())

    def ffmpeg_run():
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".mp4") as vf, tempfile.NamedTemporaryFile(suffix=".mp3") as af:
            vf.write(video_temp.getbuffer())
            vf.flush()
            subprocess.run([
                "ffmpeg", "-y", "-i", vf.name,
                "-vn", "-ab", "192k", "-ar", "44100",
                "-f", "mp3", af.name
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            af.seek(0)
            mp3_bytes.write(af.read())

    await asyncio.to_thread(ffmpeg_run)
    mp3_bytes.seek(0)
    return mp3_bytes if mp3_bytes.getbuffer().nbytes > 0 else None

# ===================================================
# دانلود مستقیم از اینستاگرام و ارسال با دکمه‌ها
# ===================================================
async def instagram_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    url = update.message.text.strip()
    chat_id = update.effective_chat.id

    if "instagram.com" not in url:
        return

    msg = await update.message.reply_text("⬇️ در حال دانلود از Instagram ...")

    import tempfile
    # کوکی موقت
    with tempfile.NamedTemporaryFile("w+", suffix=".txt") as cookie_file:
        cookie_file.write(INSTAGRAM_COOKIES.strip())
        cookie_file.flush()

        ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "noplaylist": False,
            "quiet": True,
            "cookiefile": cookie_file.name,
            "outtmpl": "-",  # استفاده از stdout
            "merge_output_format": "mp4",
            "ignoreerrors": True
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info is None:
                    await msg.edit_text("❌ امکان دانلود این پست وجود ندارد.")
                    return

                entries = info.get("entries", [info])

                for idx, entry in enumerate(entries):
                    # دانلود ویدیو یا عکس در حافظه
                    video_bytes = BytesIO()
                    def download_video():
                        ydl.download([entry["webpage_url"]])
                        filename = ydl.prepare_filename(entry)
                        with open(filename, "rb") as f:
                            video_bytes.write(f.read())
                    await asyncio.to_thread(download_video)
                    video_bytes.seek(0)

                    # دکمه‌ها
                    keyboard = InlineKeyboardMarkup([[
                        InlineKeyboardButton("➕ افزودن به گروه", url="https://t.me/AFGR63_bot?startgroup=true"),
                        InlineKeyboardButton("🎵 دانلود صوت", callback_data=f"audio_{idx}")
                    ]])

                    ext = entry.get("ext", "mp4").lower()
                    if ext in ["jpg", "jpeg", "png", "webp"]:
                        await update.message.reply_photo(
                            photo=video_bytes,
                            caption=f"🖼 {entry.get('title', 'Instagram Photo')}",
                            reply_markup=keyboard
                        )
                    else:
                        await update.message.reply_video(
                            video=video_bytes,
                            caption=f"🎬 {entry.get('title', 'Instagram Video')}",
                            reply_markup=keyboard
                        )

                    # ذخیره video_bytes در context برای استفاده در callback
                    context.chat_data[f"video_{idx}"] = video_bytes

        except Exception as e:
            await msg.edit_text(f"❌ خطا در دانلود از اینستاگرام: {e}")

    await msg.delete()

# ===================================================
# هندلر دکمه صوتی
# ===================================================
async def audio_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    data = query.data  # audio_0, audio_1, ...

    idx = data.split("_")[1]
    video_bytes = context.chat_data.get(f"video_{idx}")
    if not video_bytes:
        await query.edit_message_caption(caption="❌ ویدیو یافت نشد!")
        return

    # تبدیل ویدیو به MP3
    mp3_bytes = await convert_to_mp3_bytes(video_bytes)
    if mp3_bytes:
        await context.bot.send_audio(chat_id, mp3_bytes, caption="🎵 صوت ویدیو")
    else:
        await query.edit_message_caption(caption="❌ خطا در تولید صوت!")

# ===================================================
# اضافه کردن هندلر callback
# ===================================================
# dispatcher.add_handler(CallbackQueryHandler(audio_callback, pattern=r"^audio_"))
