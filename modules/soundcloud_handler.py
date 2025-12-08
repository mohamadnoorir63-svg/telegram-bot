# -*- coding: utf-8 -*-
"""
SoundCloud / YouTube music handler (Turbo + Cache)
Compatible with python-telegram-bot 20.7 (async)
"""

import os
import asyncio
import yt_dlp
from concurrent.futures import ProcessPoolExecutor

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

# استفاده از ProcessPoolExecutor برای استفاده از تمام هسته‌های CPU
executor = ProcessPoolExecutor(max_workers=os.cpu_count() or 4)

# ذخیره‌ی نتایج جستجو برای هر چت (لیست ترک‌ها + زبان)
# track_store[chat_id] = {"lang": "fa/en/ar", "tracks": [ ... ]}
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
        "notfound_sc": "❌ در SoundCloud نتیجه‌ای یافت نشد.",
        "download_error": "❌ در دانلود آهنگ خطایی رخ داد.",
        "track_not_found": "❌ آهنگ پیدا نشد.",
    },
    "en": {
        "searching": "🔍 Searching... please wait",
        "downloading": "⬇️ Downloading...",
        "select_song": "🎵 {n} songs found — choose one:",
        "notfound": "❌ No results in SoundCloud. Searching YouTube...",
        "notfound_sc": "❌ No SoundCloud results.",
        "download_error": "❌ Error while downloading the track.",
        "track_not_found": "❌ Track not found.",
    },
    "ar": {
        "searching": "🔍 جاري البحث ... يرجى الانتظار",
        "downloading": "⬇️ جاري تنزيل الأغنية...",
        "select_song": "🎵 تم العثور على {n} أغنية — يرجى الاختيار:",
        "notfound": "❌ لا توجد نتائج في ساوند كلاود. يتم البحث في يوتيوب...",
        "notfound_sc": "❌ لا توجد نتائج في ساوند كلاود.",
        "download_error": "❌ حدث خطأ أثناء تنزيل الأغنية.",
        "track_not_found": "❌ لم يتم العثور على الأغنية.",
    },
}

# ================================
# تابع چک مدیر بودن
# ================================
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
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
# تنظیمات مشترک yt_dlp (سریع و موازی)
# ================================
BASE_YTDLP_OPTS = {
    "quiet": True,
    "format": "bestaudio/best",
    "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
    "noprogress": True,
    "nopart": True,
    "retries": 20,
    "fragment_retries": 20,
    "concurrent_fragment_downloads": 20,  # دانلود موازی قطعه‌ها → سرعت بالا
    "overwrites": True,
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }
    ],
}


# ================================
# کمک‌کننده: پیدا کردن مسیر mp3 از روی id (کش)
# ================================
def _find_mp3_by_id(track_id):
    """
    به صورت سریع در پوشه downloads دنبال فایلی می‌گردد که با id شروع شده و mp3 باشد.
    """
    if not track_id:
        return None

    expected = os.path.join(DOWNLOAD_FOLDER, f"{track_id}.mp3")
    if os.path.exists(expected):
        return expected

    # اگر نام فایل کمی متفاوت باشد اما با id شروع شود
    try:
        for fname in os.listdir(DOWNLOAD_FOLDER):
            if fname.startswith(str(track_id)) and fname.endswith(".mp3"):
                return os.path.join(DOWNLOAD_FOLDER, fname)
    except FileNotFoundError:
        pass

    return None


# ================================
# جستجو در SoundCloud (فوق‌سریع)
# ================================
def _sc_search_sync(query: str):
    """
    جستجوی سریع در SoundCloud (۳ نتیجه برای سرعت بالاتر)
    """
    opts = {"quiet": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(f"scsearch3:{query}", download=False)


# ================================
# دانلود از SoundCloud (بدون تبدیل جداگانه)
# ================================
def _sc_download_sync(webpage_url: str):
    """
    دانلود ترک از SoundCloud و تبدیل مستقیم به mp3 با postprocessor
    """
    opts = BASE_YTDLP_OPTS.copy()
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(webpage_url, download=True)
        track_id = info.get("id")
        mp3_path = _find_mp3_by_id(track_id)

        if not mp3_path:
            # fallback: اگر فایل mp3 پیدا نشد، از نام خروجی yt_dlp استفاده می‌کنیم
            filename = ydl.prepare_filename(info)
            base, _ = os.path.splitext(filename)
            mp3_path = base + ".mp3"

        return info, mp3_path


# ================================
# fallback یوتیوب
# ================================
def _youtube_fallback_sync(query: str):
    """
    وقتی SoundCloud نتیجه ندارد → از یوتیوب mp3 می‌گیریم
    """
    opts = BASE_YTDLP_OPTS.copy()

    # استفاده از کوکی (اگر فایل وجود داشته باشد)
    if os.path.exists(COOKIE_FILE):
        opts["cookiefile"] = COOKIE_FILE

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(f"ytsearch1:{query}", download=True)
        if "entries" in info:
            info = info["entries"][0]

        vid_id = info.get("id")
        mp3_path = _find_mp3_by_id(vid_id)
        if not mp3_path:
            filename = ydl.prepare_filename(info)
            base, _ = os.path.splitext(filename)
            mp3_path = base + ".mp3"

        return info, mp3_path


# ================================
# هندلر اصلی جستجو و لیست آهنگ‌ها
# ================================
async def soundcloud_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    تریگرها:
    - "آهنگ [اسم]"
    - "music [name]"
    - "اغنية [اسم]"
    - "أغنية [اسم]"
    """
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    lowered = text.lower()

    triggers = ["آهنگ ", "music ", "اغنية ", "أغنية "]

    if not any(lowered.startswith(t) for t in triggers):
        return

    # محدودیت دسترسی در گروه (سکوت برای کاربران عادی)
    chat = update.effective_chat
    if chat.type != "private":
        allowed = await is_admin(update, context)
        if not allowed:
            return  # سکوت کامل، بدون جواب

    # تعیین زبان و query
    lang = "fa"
    query = ""
    for t in triggers:
        if lowered.startswith(t):
            query = text[len(t):].strip()
            if t.startswith("music"):
                lang = "en"
            elif "غ" in t:
                lang = "ar"
            else:
                lang = "fa"
            break

    if not query:
        return

    msg = await update.message.reply_text(LANG_MESSAGES[lang]["searching"])

    loop = asyncio.get_running_loop()

    # جستجو در SoundCloud با ProcessPoolExecutor
    try:
        sc_info = await loop.run_in_executor(executor, _sc_search_sync, query)
    except Exception:
        sc_info = None

    entries = []
    if sc_info and isinstance(sc_info, dict):
        entries = sc_info.get("entries") or []

    # اگر SoundCloud نتیجه نداشت → مستقیم یوتیوب
    if not entries:
        await msg.edit_text(LANG_MESSAGES[lang]["notfound"])
        try:
            yt_info, mp3_path = await loop.run_in_executor(
                executor, _youtube_fallback_sync, query
            )
        except Exception as e:
            await msg.edit_text(
                f"❌ {LANG_MESSAGES[lang]['download_error']}\n\n{e}"
            )
            return

        if not mp3_path or not os.path.exists(mp3_path):
            await msg.edit_text(LANG_MESSAGES[lang]["download_error"])
            return

        # ارسال آهنگ (فایل را حذف نمی‌کنیم → کش برای دفعات بعدی)
        with open(mp3_path, "rb") as f:
            await update.message.reply_audio(
                audio=f,
                caption=f"🎵 {yt_info.get('title', 'Music')}",
            )

        # در حالت Cache، فایل را نگه می‌داریم
        await msg.delete()
        return

    # ساخت لیست ساده‌شده فقط با اطلاعات لازم
    simple_tracks = []
    for t in entries:
        if not t:
            continue
        simple_tracks.append(
            {
                "id": str(t.get("id")),
                "title": t.get("title", "No title"),
                "webpage_url": t.get("webpage_url") or t.get("url"),
            }
        )

    # ذخیره در حافظه‌ی موقت: ترک‌ها + زبان
    track_store[chat.id] = {"lang": lang, "tracks": simple_tracks}

    # ساخت کیبورد انتخاب
    keyboard = []
    for t in simple_tracks:
        tid = t.get("id")
        if not tid:
            continue
        title = t.get("title") or "No title"
        # کوتاه کردن عنوان برای جلوگیری از خطای طول زیاد
        title = title[:60]
        keyboard.append(
            [InlineKeyboardButton(title, callback_data=f"music_select:{tid}")]
        )

    await msg.edit_text(
        LANG_MESSAGES[lang]["select_song"].format(n=len(simple_tracks)),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ================================
# انتخاب آهنگ و دانلود
# ================================
async def music_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    هندلر CallbackQuery برای انتخاب آهنگ از لیست
    callback_data با الگوی:  "music_select:<id>"
    """
    cq = update.callback_query
    if not cq:
        return

    chat = cq.message.chat

    # محدودیت در گروه (بدون پیام برای کاربران عادی)
    allowed = await is_admin(update, context)
    if chat.type != "private" and not allowed:
        await cq.answer()  # فقط پاسخ callback بدون پیام
        return  # سکوت کامل

    await cq.answer()

    data = cq.data or ""
    if ":" not in data:
        return

    prefix, track_id = data.split(":", 1)
    if prefix != "music_select":
        return

    chat_id = chat.id
    store = track_store.get(chat_id)
    if not store:
        await cq.edit_message_text(LANG_MESSAGES["fa"]["track_not_found"])
        return

    lang = store.get("lang", "fa")
    tracks = store.get("tracks") or []

    # پیدا کردن ترک انتخاب شده
    track = next(
        (t for t in tracks if str(t.get("id")) == str(track_id)),
        None
    )
    if not track:
        await cq.edit_message_text(LANG_MESSAGES[lang]["track_not_found"])
        return

    msg = await cq.edit_message_text(LANG_MESSAGES[lang]["downloading"])

    loop = asyncio.get_running_loop()

    try:
        # قبل از دانلود، چک کن آیا mp3 کش شده وجود دارد یا نه
        cached_mp3 = _find_mp3_by_id(str(track_id))
        if cached_mp3 and os.path.exists(cached_mp3):
            info = {"title": track.get("title")}
            mp3_path = cached_mp3
        else:
            info, mp3_path = await loop.run_in_executor(
                executor, _sc_download_sync, track["webpage_url"]
            )
    except Exception as e:
        await msg.edit_text(
            f"❌ {LANG_MESSAGES[lang]['download_error']}\n\n{e}"
        )
        return

    if not mp3_path or not os.path.exists(mp3_path):
        await msg.edit_text(LANG_MESSAGES[lang]["download_error"])
        return

    # ارسال فایل (Cache: فایل را حذف نمی‌کنیم)
    with open(mp3_path, "rb") as f:
        await context.bot.send_audio(
            chat_id,
            f,
            caption=f"🎵 {info.get('title') or track.get('title')}",
        )

    await msg.delete()
