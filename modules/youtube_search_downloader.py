import os
import re
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

import yt_dlp
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

SUDO_USERS = [8588347189]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOWNLOAD_FOLDER = os.path.join(BASE_DIR, "downloads")
COOKIE_FILE = os.path.join(BASE_DIR, "modules", "youtube_cookie.txt")

MAX_FILE_SIZE = 800 * 1024 * 1024

os.makedirs(os.path.dirname(COOKIE_FILE), exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

COOKIE_DATA = r"""
# Netscape HTTP Cookie File
# https://curl.haxx.se/rfc/cookie_spec.html
# This is a generated file! Do not edit.

# کوکی کامل YouTube را اینجا Paste کن
"""
# Netscape HTTP Cookie File
# https://curl.haxx.se/rfc/cookie_spec.html
# This is a generated file! Do not edit.

.youtube.com	TRUE	/	TRUE	1799284338	SOCS	CAISNQgDEitib3FfaWRlbnRpdHlmcm9udGVuZHVpc2VydmVyXzIwMjUxMjAzLjA4X3AwGgJkZSACGgYIgKrYyQY
.youtube.com	TRUE	/	TRUE	1780708338	VISITOR_INFO1_LIVE	OBpYWqO2PUs
.youtube.com	TRUE	/	TRUE	1780708338	__Secure-BUCKET	CMwB
.youtube.com	TRUE	/	TRUE	1799716339	LOGIN_INFO	AFmmF2swRQIgYVveaSordutJGSFaMl84shpElRnOPoIJgsy-CxerUAICIQD-N79Q6VXrD9fAWQSUENWRJGYd-rZwrVEXNZ9Fbim1Ng:QUQ3MjNmeWdnTGZhMDdETlh0VnZJSjdQTmlsdlNLT25wQjdMR0V4RDhjbTNPQmdpc1BkT2ZjTzdaeUFFbGpmOGl6dVJiZ0Z4aXpnTXRlZ0hOaFFyZmdPaVhSSUotdEpxYjZBUWxIR1VpbzdENW5YZk9VUWUyU09MVDhlYVJLSW5Ua2dIX0NxUE1reC01cXJiZ3Q5Q2k1WHEzQjFTWUU1X2JR
.youtube.com	TRUE	/	FALSE	1799902985	SID	g.a0004Qh-SyGsKnh8jK0W8abn607R1S57deRp4xAuoGuSyRoyjhy0873JEYZeawVWl1V8fWZ3yAACgYKAcsSARISFQHGX2MiKoRExCpwFo1j0Z2uWxlVUBoVAUF8yKoCTcwmJwJ3RR0AdknIa2X50076
.youtube.com	TRUE	/	TRUE	1799902985	__Secure-1PSID	g.a0004Qh-SyGsKnh8jK0W8abn607R1S57deRp4xAuoGuSyRoyjhy08cLiOpa6QvgO36aY8klWZgACgYKAYESARISFQHGX2MiU0SzeJZC32XQec7taO4fxhoVAUF8yKpFB12uvfXu4rLqEQefZpRZ0076
.youtube.com	TRUE	/	TRUE	1799902985	__Secure-3PSID	g.a0004Qh-SyGsKnh8jK0W8abn607R1S57deRp4xAuoGuSyRoyjhy0dv2lIWUBJzJaBA1sqO54uAACgYKAXgSARISFQHGX2Mi8ac0ChIXv4A2jf5p9urOTRoVAUF8yKoSVZCW7nP5DTelIPs-Eof_0076
.youtube.com	TRUE	/	FALSE	1799902985	HSID	ACot7wsidbZkE1cpX
.youtube.com	TRUE	/	TRUE	1799902985	SSID	ADvnhaZMQnQ0bacl-
.youtube.com	TRUE	/	FALSE	1799902985	APISID	m-DWZeLhqcxzseLm/APqdatThKfQoxN_ZP
.youtube.com	TRUE	/	TRUE	1799902985	SAPISID	l6jBIc-jxjFq-2tm/AOyKuClMF0-1v6JIZ
.youtube.com	TRUE	/	TRUE	1799902985	__Secure-1PAPISID	l6jBIc-jxjFq-2tm/AOyKuClMF0-1v6JIZ
.youtube.com	TRUE	/	TRUE	1799902985	__Secure-3PAPISID	l6jBIc-jxjFq-2tm/AOyKuClMF0-1v6JIZ
.youtube.com	TRUE	/	TRUE	1796878985	__Secure-1PSIDTS	sidts-CjUBflaCdbjZgNKbdvEZh-mKCYMD-QE6Z336jix30OspuuLGc8NRnhCuCeW9n65rlA_5Z1qMeBAA
.youtube.com	TRUE	/	TRUE	1796878985	__Secure-3PSIDTS	sidts-CjUBflaCdbjZgNKbdvEZh-mKCYMD-QE6Z336jix30OspuuLGc8NRnhCuCeW9n65rlA_5Z1qMeBAA
.youtube.com	TRUE	/	FALSE	1799958016	_ga	GA1.1.1553215078.1765398016
.youtube.com	TRUE	/	FALSE	1799958049	_ga_VCGEPY40VB	GS2.1.s1765398016$o1$g1$t1765398048$j28$l0$h0
.youtube.com	TRUE	/	TRUE	1799969026	PREF	tz=Europe.Berlin&repeat=NONE&autoplay=true
.youtube.com	TRUE	/	FALSE	1796945280	SIDCC	AKEyXzVUZsZSKhU_vzRuar-0gYaho5C-mhoQKeUL95KIaGK4_Ah9PkP8JcTNe0JZ-QK4Ep3C
.youtube.com	TRUE	/	TRUE	1796945280	__Secure-1PSIDCC	AKEyXzWw-0sa09atGWedvIRv3ZfJ5bLhxjE4_ZNHhoe7KxpRqDVu4704VoO_N7DkWfTm8fk1
.youtube.com	TRUE	/	TRUE	1796945280	__Secure-3PSIDCC	AKEyXzUnlMIQ68ThuB5D_XS5ibbQivq0Fe_IaS_P8DqPPA6eT0fjLWKSAbnaz8_M0mx7u9S9

with open(COOKIE_FILE, "w", encoding="utf-8") as f:
    f.write(COOKIE_DATA.strip() + "\n")

URL_RE = re.compile(r"(https?://[^\s]+)")
executor = ThreadPoolExecutor(max_workers=3)

pending_links = {}
download_queue = asyncio.Queue()


async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    user = update.effective_user

    if not chat or not user:
        return False

    if chat.type == "private":
        return True

    if user.id in SUDO_USERS:
        return True

    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        return member.status in ("creator", "administrator")
    except Exception:
        return False


def cleanup_temp():
    now = time.time()
    for name in os.listdir(DOWNLOAD_FOLDER):
        path = os.path.join(DOWNLOAD_FOLDER, name)
        try:
            if os.path.isfile(path) and now - os.path.getmtime(path) > 600:
                os.remove(path)
        except Exception:
            pass


def find_file(video_id, exts):
    for ext in exts:
        path = os.path.join(DOWNLOAD_FOLDER, f"{video_id}.{ext}")
        if os.path.exists(path):
            return path
    return None


def audio_opts():
    return {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "format": "140/251/250/249/bestaudio/best",
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
        "retries": 10,
        "fragment_retries": 10,
        "nopart": True,
        "overwrites": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"]
            }
        },
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }


def video_opts():
    return {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "format": "18/best",
        "merge_output_format": "mp4",
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
        "retries": 10,
        "fragment_retries": 10,
        "nopart": True,
        "overwrites": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"]
            }
        },
    }


def _download_audio_sync(url: str):
    with yt_dlp.YoutubeDL(audio_opts()) as ydl:
        info = ydl.extract_info(url, download=True)

    if not info or "id" not in info:
        raise RuntimeError("استخراج اطلاعات صوت ناموفق بود.")

    path = find_file(info["id"], ["mp3", "m4a", "webm", "opus"])

    if not path:
        raise FileNotFoundError("فایل صوتی ساخته نشد.")

    return info, path


def _download_video_sync(url: str):
    with yt_dlp.YoutubeDL(video_opts()) as ydl:
        info = ydl.extract_info(url, download=True)

    if not info or "id" not in info:
        raise RuntimeError("استخراج اطلاعات ویدیو ناموفق بود.")

    path = find_file(info["id"], ["mp4", "webm", "mkv"])

    if not path:
        raise FileNotFoundError("فایل ویدیو ساخته نشد.")

    return info, path


async def youtube_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    match = URL_RE.search(text)

    if not match:
        return

    url = match.group(1)

    if "youtube.com" not in url and "youtu.be" not in url:
        return

    if update.effective_chat.type != "private":
        if not await is_admin(update, context):
            return

    pending_links[update.effective_chat.id] = url

    keyboard = [
        [
            InlineKeyboardButton("🎵 دانلود صوت MP3", callback_data="yt_audio"),
            InlineKeyboardButton("🎬 دانلود ویدیو MP4", callback_data="yt_video"),
        ]
    ]

    await update.message.reply_text(
        "⬇️ نوع دانلود را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def youtube_download_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query

    if not cq:
        return

    await cq.answer()

    chat_id = cq.message.chat.id

    if cq.message.chat.type != "private":
        member = await context.bot.get_chat_member(chat_id, cq.from_user.id)
        if cq.from_user.id not in SUDO_USERS and member.status not in ("creator", "administrator"):
            return await cq.answer("⛔ فقط مدیران گروه مجاز هستند.", show_alert=True)

    url = pending_links.get(chat_id)

    if not url:
        return await cq.edit_message_text("❌ لینک پیدا نشد. دوباره لینک یوتیوب را بفرست.")

    await download_queue.put({
        "chat_id": chat_id,
        "message_id": cq.message.message_id,
        "url": url,
        "mode": cq.data,
    })

    await cq.edit_message_text("⏳ لینک شما به صف دانلود اضافه شد. لطفاً منتظر بمانید...")


async def download_worker(bot):
    while True:
        item = await download_queue.get()

        chat_id = item["chat_id"]
        message_id = item["message_id"]
        url = item["url"]
        mode = item["mode"]

        cleanup_temp()
        loop = asyncio.get_running_loop()

        try:
            if mode == "yt_audio":
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text="🎵 در حال دانلود و تبدیل به MP3..."
                )

                info, audio_path = await loop.run_in_executor(executor, _download_audio_sync, url)

                if os.path.getsize(audio_path) > MAX_FILE_SIZE:
                    os.remove(audio_path)
                    await bot.send_message(chat_id, "❌ حجم فایل صوتی بیشتر از 800MB است.")
                    continue

                title = info.get("title") or "YouTube Audio"

                with open(audio_path, "rb") as f:
                    await bot.send_audio(
                        chat_id=chat_id,
                        audio=f,
                        title=title,
                        caption=f"🎵 {title}",
                        read_timeout=180,
                        write_timeout=180,
                        connect_timeout=60,
                    )

                os.remove(audio_path)

            elif mode == "yt_video":
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text="🎬 در حال دانلود ویدیو MP4..."
                )

                info, video_path = await loop.run_in_executor(executor, _download_video_sync, url)

                if os.path.getsize(video_path) > MAX_FILE_SIZE:
                    os.remove(video_path)
                    await bot.send_message(chat_id, "❌ حجم ویدیو بیشتر از 800MB است.")
                    continue

                title = info.get("title") or "YouTube Video"

                with open(video_path, "rb") as f:
                    await bot.send_video(
                        chat_id=chat_id,
                        video=f,
                        caption=f"🎬 {title}",
                        supports_streaming=True,
                        read_timeout=180,
                        write_timeout=180,
                        connect_timeout=60,
                    )

                os.remove(video_path)

            try:
                await bot.delete_message(chat_id, message_id)
            except Exception:
                pass

        except Exception as e:
            try:
                await bot.send_message(chat_id, f"❌ خطا در دانلود:\n{e}")
            except Exception:
                pass

        finally:
            cleanup_temp()
            download_queue.task_done()
