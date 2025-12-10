# modules/youtube_mp3_handler.py

import re
import os
import yt_dlp
import asyncio
from typing import Dict
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# ================================
# تنظیمات
# ================================
SUDO_USERS = [8588347189]  # در صورت نیاز استفاده کن

# کوکی مستقیماً داخل کد قرار دارد
YOUTUBE_COOKIE_DATA = """# Netscape HTTP Cookie File
# https://curl.haxx.se/rfc/cookie_spec.html
# This is a generated file! Do not edit.

.youtube.com	TRUE	/	TRUE	1799284338	SOCS	CAISNQgDEitib3FfaWRlbnRpdHlmcm9udGVpc2VydmlyXzIwMjUxMjAzLjA4X3AwGgJkZSACGgYIgKrYyQY
.youtube.com	TRUE	/	TRUE	1780708338	VISITOR_INFO1_LIVE	OBpYWqO2PUs
.youtube.com	TRUE	/	TRUE	1780708338	__Secure-BUCKET	CMwB
.youtube.com	TRUE	/	TRUE	1799716339	LOGIN_INFO	AFmmF2swRQIgYVveaSordutJGSFaMl84shpElRnOPoIJgsy-CxerUAICIQD-N79Q6VXrD9fAWQSUENWRJGYd-rZwrVEXNZ9Fbim1Ng:QUQ3MjNmeWdnTGZhMDdETlh0VnZJSjdQTmlsdlNLT25wQjdMR0V4RDhjbTNPQmdpc1BkT2ZjTzdaeUFFbGpmOGl6dVJiZ0Z4aXpnTXRlZ0hOaFFyZmdPaVhSSUotdEpxYjZBUWxIR1VpbzdENW5YZk9VUWUyU09MVDhlYVJLSW5Ua2dIX0NxUE1reC01cXJiZ3Q5Q2k1WHEzQjFTWUU1X2JR
.youtube.com	TRUE	/	FALSE	1799902985	SID	g.a0004Qh-SyGsKnh8jK0W8abn607R1S57deRp4xAuoGuSyRoyjhy0873JEYZeawVWl1V8fWZ3yAACgYKAcsSARISFQHGX2MiKoRExCpwFo1j0Z2uWxlVUBoVAUF8yKoCTcwmJwJ3RR0AdknIa2X50076
.youtube.com	TRUE	/	TRUE	1799902985	__Secure-1PSID	g.a0004Qh-SyGsKnh8jK0W8abn607R1S57deRp4xAuoGuSyRoyjhy08cLiOpa6QvgO36aY8klWZgACgYKAYESARISFQHGX2MiU0SzeJZC32XQec7taO4fxhoVAUF8yKpFB12uvfXu4rLqEQefZpRZ0076
.youtube.com	TRUE	/	TRUE	1799902985	__Secure-3PSID	g.a0004Qh-SyGsKnh8jK0W8abn607R1S57deRp4xAuoGuSyRoyjhy0dv2lIWUBJzJaBA1sqO54uAACgYKAXgSARISFQHGX2Mi8ac0ChIXv4A2jf5p9urOTRoVAUF8yKoSVZCW7nP5DTelIPs-Eof_0076
"""

# مسیرها
MODULES_FOLDER = "modules"
COOKIE_FILE = os.path.join(MODULES_FOLDER, "youtube_cookie.txt")
DOWNLOAD_FOLDER = "downloads"
os.makedirs(MODULES_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# ذخیره کوکی (یکبار)
with open(COOKIE_FILE, "w", encoding="utf-8") as _f:
    _f.write(YOUTUBE_COOKIE_DATA.strip())

# regex برای لینک
URL_RE = re.compile(r"(https?://[^\s]+)")

# نگهداری نتایج جستجو برای callbackها
# key = original_message_id (int) -> dict video_id -> metadata (title, webpage_url)
pending_search_results: Dict[int, Dict[str, Dict]] = {}

# دکمه افزودن ربات به گروه (فقط در پیوی استفاده می‌شود)
def add_bot_button(chat_type: str):
    if chat_type == "private":
        return InlineKeyboardMarkup(
            [[InlineKeyboardButton("➕ افزودن ربات به گروه", url="https://t.me/AFGR63_bot?startgroup=true")]]
        )
    return None

# کمک‌کننده: اگر yt-dlp اسم فایل را با پسوند نامشخص ساخت (.NA یا بدون ext)، آن را اصلاح کن
def resolve_downloaded_file(ydl, info) -> str:
    """
    برمی‌گرداند مسیر واقعی فایل دانلود شده (با پسوند درست).
    ydl.prepare_filename(info) -> base (with ext)
    در صورت .NA یا نامشخص سعی می‌کند با پسوندهای رایج چک کند.
    """
    base = ydl.prepare_filename(info)  # ممکن است e.g. "title.NA" یا "title"
    # معمولاً prepare_filename شامل ext است: base = "... .ext"
    mpath = base
    # اگر base فاقد پسوند باشد یا .NA داشت، تلاش برای یافتن پسوندهای رایج
    if not os.path.splitext(base)[1] or base.endswith(".NA"):
        # نام بدون .NA
        base_no_na = base.replace(".NA", "")
        candidates = [
            base_no_na + ext for ext in (".m4a", ".webm", ".mp4", ".opus", ".ogg", ".aac")
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        # شاید فایل بدون ext ساخته شده باشد (rare), تلاش کنیم نام بدون ext را موجود پیدا کنیم
        if os.path.exists(base_no_na):
            # سعی کن با یک ext پیش‌فرض صدا بدی
            newname = base_no_na + ".m4a"
            try:
                os.rename(base_no_na, newname)
                return newname
            except Exception:
                pass
        # در نهایت اگر هیچ‌کدام نبود، برمی‌گردونیم base_no_na + .m4a (ممکنه بعداً وجود نداشته باشه)
        return base_no_na + ".m4a"
    else:
        # base شامل پسوند است
        if os.path.exists(base):
            return base
        # فایل با همون base ممکنه با یک ext متفاوت ساخته شده باشه
        base_root = os.path.splitext(base)[0]
        for ext in (".m4a", ".webm", ".mp4", ".opus", ".ogg", ".aac"):
            cand = base_root + ext
            if os.path.exists(cand):
                return cand
        # fallback: برگردان base (حتی اگر وجود نداشته باشه)
        return base

# تابع دانلود مستقیم بدون تبدیل (bestaudio)
def download_direct_audio_by_url(url_or_search: str, max_search_results: int = 5):
    """
    اگر url_or_search لینک مستقیم بود، دانلود همان ویدیو.
    اگر متن بود، ابتدا با ytsearchN نتایج را می‌گیرد و
    برای حالت "اولین نتیجه" همان اولین مورد را دانلود می‌کند.
    returns: (filepath, info)
    """
    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "cookiefile": COOKIE_FILE,
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s"),
        "noplaylist": True,
        "ignoreerrors": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # اگر یک لینک کامل است -> مستقیم استخراج و دانلود
        if URL_RE.match(url_or_search):
            info = ydl.extract_info(url_or_search, download=True)
            filepath = resolve_downloaded_file(ydl, info)
            return filepath, info

        # اگر متن است -> جستجو، اولین نتیجه قابل دانلود را انتخاب کن
        search = f"ytsearch{max_search_results}:{url_or_search}"
        search_info = ydl.extract_info(search, download=False)
        entries = search_info.get("entries") or []
        if not entries:
            raise RuntimeError("هیچ نتیجه‌ای برای این جستجو یافت نشد.")

        last_exc = None
        for entry in entries:
            # هر entry ممکنه metadata باشه؛ آدرس صفحه را بگیر
            vid_url = entry.get("webpage_url") or f"https://www.youtube.com/watch?v={entry.get('id')}"
            try:
                info = ydl.extract_info(vid_url, download=True)
                filepath = resolve_downloaded_file(ydl, info)
                if os.path.exists(filepath):
                    return filepath, info
                # اگر فایل وجود نداشت، ادامه بده روی ورودی بعدی
            except Exception as exc:
                last_exc = exc
                continue

        # اگر همه ناموفق بودند، بالاخره last_exc را بالا بنداز
        if last_exc:
            raise last_exc
        raise RuntimeError("هیچ‌یک از نتایج قابل دانلود نبودند.")

# تابع فقط گرفتن لیست نتایج (بدون دانلود) برای نمایش دکمه‌ها
def search_youtube(query: str, limit: int = 5):
    ydl_opts = {
        "quiet": True,
        "cookiefile": COOKIE_FILE,
        "noplaylist": True,
        "ignoreerrors": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
        entries = info.get("entries") or []
        results = []
        for e in entries:
            vid = str(e.get("id") or "")
            title = e.get("title") or vid
            url = e.get("webpage_url") or f"https://www.youtube.com/watch?v={vid}"
            results.append({"id": vid, "title": title, "url": url})
        return results

# ================================
# هندلر پیام متنی (مدل 1 + 2)
# ================================
async def youtube_mp3_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    منطق:
    - اگر پیام کمتر از 3 کلمه بود -> مدل 1: اولین نتیجه را مستقیم دانلود و ارسال کن.
    - اگر پیام 3 کلمه یا بیشتر بود -> مدل 2: لیست 5 نتیجه را نشان بده (دکمه) و کاربر انتخاب کند.
    """
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    if not text:
        return

    # پاسخ اولیه
    info_msg = await update.message.reply_text("🔎 در حال جستجو...")

    words = [w for w in text.split() if w.strip()]
    try:
        if len(words) >= 3:
            # مدل 2: نمایش 5 نتیجه برای انتخاب
            results = await asyncio.get_running_loop().run_in_executor(None, search_youtube, text, 5)
            if not results:
                await info_msg.edit_text("⌛ نتیجه‌ای پیدا نشد.")
                return

            # ذخیره نتایج با استفاده از message_id پیام فعلی (تا callback آن را بازیابی کند)
            orig_msg_id = update.message.message_id
            # ذخیره با key orig_msg_id
            pending_search_results[orig_msg_id] = {r["id"]: r for r in results}

            # ساخت کیبورد دکمه‌ها
            keyboard = []
            for r in results:
                keyboard.append([InlineKeyboardButton(r["title"][:60], callback_data=f"yt_pick:{orig_msg_id}:{r['id']}")])

            # دکمه افزودن ربات فقط در پیوی
            reply_markup = InlineKeyboardMarkup(keyboard)
            await info_msg.edit_text(f"🎵 {len(results)} نتیجه یافت شد — یک مورد را انتخاب کنید:", reply_markup=reply_markup)
            return
        else:
            # مدل 1: دانلود اولین نتیجه و ارسال مستقیم
            await info_msg.edit_text("⬇️ در حال دانلود اولین نتیجه...")
            file_path, info = await asyncio.get_running_loop().run_in_executor(None, download_direct_audio_by_url, text, 5)
            if not os.path.exists(file_path):
                await info_msg.edit_text("❌ فایل خروجی پیدا نشد.")
                return

            # ارسال فایل صوتی همان فرمت اصلی (telegram reply_audio)
            await update.message.reply_audio(
                audio=open(file_path, "rb"),
                caption=f"🎵 {info.get('title', 'Music')}",
                reply_markup=add_bot_button(update.effective_chat.type)
            )
            try:
                os.remove(file_path)
            except Exception:
                pass
            await info_msg.delete()
            return

    except Exception as e:
        # لاگ در کنسول و پیام کوتاه به کاربر
        print("youtube handler error:", repr(e))
        await info_msg.edit_text("❌ خطا در جستجو یا دانلود. ممکن است ویدیو در دسترس نباشد یا کوکی نامعتبر باشد.")

# ================================
# هندلر callback از دکمه (وقتی کاربر یکی از نتایج را انتخاب می‌کند)
# ================================
async def youtube_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    if not cq or not cq.data:
        return
    await cq.answer()  # تایید callback

    # فرمت callback_data: yt_pick:{orig_msg_id}:{video_id}
    try:
        _, orig_msg_id_s, vid = cq.data.split(":", 2)
        orig_msg_id = int(orig_msg_id_s)
    except Exception:
        return await cq.edit_message_text("❌ دادهٔ دکمه نامعتبر است.")

    # واکشی متادیتا از pending_search_results
    entries = pending_search_results.get(orig_msg_id)
    if not entries or vid not in entries:
        return await cq.edit_message_text("❌ نتیجهٔ انتخاب‌شده در دسترس نیست یا منقضی شده.")

    sel = entries[vid]
    try:
        # اعلام به کاربر و شروع دانلود
        await cq.edit_message_text(f"⬇️ در حال دانلود: {sel['title']}")
        file_path, info = await asyncio.get_running_loop().run_in_executor(None, download_direct_audio_by_url, sel["url"], 5)

        if not os.path.exists(file_path):
            return await cq.edit_message_text("❌ فایل دانلود نشد.")

        # ارسال فایل (اگر در یک چت خصوصی است، دکمه افزودن ربات هم بده)
        await context.bot.send_audio(
            cq.message.chat_id,
            audio=open(file_path, "rb"),
            caption=f"🎵 {info.get('title','Music')}",
            reply_markup=add_bot_button(cq.message.chat.type)
        )

        try:
            os.remove(file_path)
        except Exception:
            pass

        # پاک‌سازی ورودی pending
        pending_search_results.pop(orig_msg_id, None)

        # حذف پیام قبلی که دکمه‌ها را نگه داشته بود
        try:
            await cq.message.delete()
        except Exception:
            pass

    except Exception as e:
        print("callback download error:", repr(e))
        await cq.edit_message_text("❌ خطا در دانلود یا ارسال. ممکن است ویدیو ناموجود باشد یا کوکی مشکل داشته باشد.")

# ================================
# نکته: برای فعال‌سازی در فایل اصلی (bot.py) این خطوط را اضافه کن:
# from modules.youtube_mp3_handler import youtube_mp3_handler, youtube_callback_handler
# from telegram.ext import MessageHandler, CallbackQueryHandler, filters
# application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, youtube_mp3_handler), group=4000)
# application.add_handler(CallbackQueryHandler(youtube_callback_handler, pattern=r"^yt_pick:"), group=4000)
# ================================
