# modules/soundcloud_handler.py

import os
import asyncio
import subprocess
import yt_dlp
from concurrent.futures import ThreadPoolExecutor

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# ================================
# سودوها
# ================================

SUDO_USERS = [8588347189]   # ← آیدی شما

# ================================
# تنظیمات پایه
# ================================

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

COOKIE_FILE = "modules/youtube_cookie.txt"

# همون ThreadPoolExecutor قبلی، فقط max_workers مناسب
executor = ThreadPoolExecutor(max_workers=8)

# ذخیره آهنگ‌ها برای انتخاب در callback
track_store = {}

# ================================
# پیام‌ها سه زبانه
# ================================

LANG_MESSAGES = {
    "fa": {
        "searching": "🔍 در حال جستجو ... لطفاً صبر کنید",
        "downloading": "⬇️ در حال دانلود آهنگ...",
        "select_song": "🎵 {n} آهنگ پیدا شد — لطفاً انتخاب کنید:",
        "notfound": "❌ در SoundCloud چیزی پیدا نشد. در حال جستجو در یوتیوب...",
    },
    "en": {
        "searching": "🔍 Searching... please wait",
        "downloading": "⬇️ Downloading...",
        "select_song": "🎵 {n} songs found — choose one:",
        "notfound": "❌ No results in SoundCloud. Searching YouTube...",
    },
    "ar": {
        "searching": "🔍 جاري البحث ... يرجى الانتظار",
        "downloading": "⬇️ جاري تنزيل الأغنية...",
        "select_song": "🎵 تم العثور على {n} أغنية — يرجى الاختيار:",
        "notfound": "❌ لا توجد نتائج في ساوند كلاود. يتم البحث في يوتيوب...",
    },
}

# ================================
# تنظیمات پایه‌ی yt_dlp (توربو)
# ================================

BASE_YTDLP_OPTS = {
    "format": "bestaudio/best",
    "quiet": True,
    "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
    "noprogress": True,
    "nopart": True,
    "retries": 15,
    "fragment_retries": 15,
    "concurrent_fragment_downloads": 15,  # دانلود موازی قطعه‌ها → سرعت بالا
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }
    ],
}

# ================================
# تابع چک مدیر بودن
# ================================

async def is_admin(update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    # پیوی → همه مجاز
    if chat.type == "private":
        return True

    # سودو → همیشه مجاز
    if user and user.id in SUDO_USERS:
        return True

    try:
        admins = await context.bot.get_chat_administrators(chat.id)
        admin_ids = [a.user.id for a in admins]
    except Exception:
        return False

    return bool(user and user.id in admin_ids)

# ================================
# تبدیل MP3 (الان فقط اگر خواستی جای دیگه استفاده کنی)
# ================================

def _mp3_convert_sync(filepath: str) -> str:
    """
    هنوز نگهش داشتم، ولی برای SoundCloud دیگه ازش استفاده نمی‌کنیم
    چون yt_dlp خودش مستقیماً mp3 می‌سازه.
    """
    mp3 = filepath.rsplit(".", 1)[0] + ".mp3"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            filepath,
            "-vn",
            "-ab",
            "192k",
            "-ar",
            "44100",
            mp3,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return mp3

# ================================
# دانلود از SoundCloud (سریع + بدون تبدیل جداگانه)
# ================================

def _sc_download_sync(url: str):
    """
    قبلاً:
      - فقط bestaudio می‌گرفت
      - بعد جداگانه ffmpeg اجرا می‌کردی
    الان:
      - yt_dlp خودش با postprocessor به mp3 تبدیل می‌کند
      - یک مرحله‌ی سنگین حذف شد → سرعت بالاتر
    """
    opts = BASE_YTDLP_OPTS.copy()

    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)
        # بعد از postprocessor، خروجی mp3 است
        filename = y.prepare_filename(info)
        mp3 = filename.rsplit(".", 1)[0] + ".mp3"
        return info, mp3

# ================================
# fallback یوتیوب (توربو)
# ================================

def _youtube_fallback_sync(query: str):
    """
    همان منطق قبل، فقط با تنظیمات تهاجمی‌تر برای سرعت بالاتر.
    """
    opts = BASE_YTDLP_OPTS.copy()
    opts.update(
        {
            "concurrent_fragment_downloads": 20,
        }
    )
    if os.path.exists(COOKIE_FILE):
        opts["cookiefile"] = COOKIE_FILE

    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(f"ytsearch1:{query}", download=True)
        if "entries" in info:
            info = info["entries"][0]
        filename = y.prepare_filename(info)
        mp3 = filename.rsplit(".", 1)[0] + ".mp3"
        return info, mp3

# ================================
# جستجو و لیست آهنگ‌ها
# ================================

async def soundcloud_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    triggers = ["آهنگ ", "music ", "اغنية ", "أغنية "]

    if not any(text.lower().startswith(t) for t in triggers):
        return

    # محدودیت دسترسی در گروه (سکوت برای کاربران عادی)
    if update.effective_chat.type != "private":
        allowed = await is_admin(update, context)
        if not allowed:
            return  # سکوت کامل

    # تعیین زبان
    lang = "fa"
    query = ""
    for t in triggers:
        if text.lower().startswith(t):
            query = text[len(t):].strip()
            lang = "en" if t.startswith("music") else ("ar" if "غ" in t else "fa")
            break

    if not query:
        return

    msg = await update.message.reply_text(LANG_MESSAGES[lang]["searching"])

    # جستجو در soundcloud
    def search_sc():
        # قبلاً scsearch10 بود → کندتر
        # الان scsearch3 برای سرعت بیشتر (۳ نتیجه اول معمولاً کافی‌اند)
        with yt_dlp.YoutubeDL({"quiet": True}) as y:
            return y.extract_info(f"scsearch3:{query}", download=False)

    loop = asyncio.get_running_loop()
    try:
        sc_info = await loop.run_in_executor(executor, search_sc)
    except Exception:
        sc_info = None

    # اگر نتیجه نبود → یوتیوب
    if not sc_info or "entries" not in sc_info or len(sc_info["entries"]) == 0:
        await msg.edit_text(LANG_MESSAGES[lang]["notfound"])

        try:
            yt_info, mp3_path = await loop.run_in_executor(
                executor, _youtube_fallback_sync, query
            )
        except Exception as e:
            return await msg.edit_text(f"❌ خطا:\n{e}")

        if not os.path.exists(mp3_path):
            return await msg.edit_text("❌ مشکلی در دانلود فایل یوتیوب پیش آمد.")

        with open(mp3_path, "rb") as f:
            await update.message.reply_audio(
                audio=f, caption=f"🎵 {yt_info.get('title', 'Music')}"
            )

        # اگر نمی‌خواهی فایل‌ها بمانند، این خط را نگه دار
        # (اگر کش می‌خواهی، این را کامنت کن)
        # os.remove(mp3_path)

        return

    # ساخت لیست انتخاب
    track_store[update.effective_chat.id] = sc_info["entries"]
    keyboard = [
        [InlineKeyboardButton(t["title"], callback_data=f"music_select:{t['id']}")]
        for t in sc_info["entries"]
    ]

    await msg.edit_text(
        LANG_MESSAGES[lang]["select_song"].format(n=len(sc_info["entries"])),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# ================================
# انتخاب آهنگ و دانلود
# ================================

async def music_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query

    # محدودیت در گروه (بدون پیام)
    allowed = await is_admin(update, context)
    if update.effective_chat.type != "private" and not allowed:
        return  # سکوت کامل

    await cq.answer()

    track_id = cq.data.split(":")[1]
    chat = cq.message.chat_id
    tracks = track_store.get(chat, [])

    track = next((t for t in tracks if str(t["id"]) == track_id), None)
    if not track:
        return await cq.edit_message_text("❌ آهنگ پیدا نشد.")

    msg = await cq.edit_message_text("⬇️ در حال دانلود...")

    loop = asyncio.get_running_loop()

    # قبلاً:
    #   info, file = await loop.run_in_executor(executor, _sc_download_sync, track["webpage_url"])
    #   mp3 = await loop.run_in_executor(executor, _mp3_convert_sync, file)
    # الان mp3 مستقیم از yt_dlp می‌آید → یک مرحله کمتر و سرعت بیشتر
    info, mp3 = await loop.run_in_executor(
        executor, _sc_download_sync, track["webpage_url"]
    )

    if not os.path.exists(mp3):
        return await msg.edit_text("❌ مشکل در دانلود/تبدیل فایل.")

    with open(mp3, "rb") as f:
        await context.bot.send_audio(chat, f, caption=f"🎵 {info.get('title')}")

    # اگر نمی‌خواهی کش بماند، این دو خط را فعال نگه دار
    # (برای سرعت بالاتر در درخواست‌های بعدی، می‌توانی این‌ها را کامنت کنی)
    # os.remove(mp3)

    await msg.delete()
