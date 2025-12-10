# modules/youtube_search_direct.py

import re
import asyncio
import json
from concurrent.futures import ThreadPoolExecutor

import yt_dlp
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# ================================
# سودو
# ================================
SUDO_USERS = [8588347189]  # آیدی شما

# ================================
# تنظیمات اولیه
# ================================
URL_RE = re.compile(r"(https?://[^\s]+)")
executor = ThreadPoolExecutor(max_workers=3)

# ================================
# کش YouTube (لینک مستقیم)
# ================================
YT_CACHE_FILE = "modules/yt_direct_cache.json"
try:
    with open(YT_CACHE_FILE, "r", encoding="utf-8") as f:
        YT_CACHE = json.load(f)
except:
    YT_CACHE = {}

def save_yt_cache():
    with open(YT_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(YT_CACHE, f, indent=2, ensure_ascii=False)

# ================================
# ذخیره لینک‌ها برای انتخاب نوع
# ================================
pending_links = {}

# ================================
# دکمه افزودن ربات فقط در پیوی
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
# استخراج لینک مستقیم بدون دانلود
# ================================
def _get_direct_link(url, type_="audio"):
    opts = {"quiet": True, "noplaylist": True}
    if type_ == "audio":
        opts["format"] = "bestaudio/best"
    else:
        opts["format"] = "bestvideo+bestaudio/best"

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if "entries" in info:  # playlist fallback
            info = info["entries"][0]

        if type_ == "audio":
            # پیدا کردن لینک صوتی
            for f in info["formats"]:
                if f.get("acodec") != "none" and f.get("vcodec") == "none":
                    return info, f["url"]
        else:
            # پیدا کردن لینک ویدیویی
            for f in info["formats"]:
                if f.get("vcodec") != "none" and f.get("acodec") != "none":
                    return info, f["url"]

        # fallback به لینک اصلی
        return info, info.get("url")

# ================================
# مرحله ۱ — دریافت لینک و نمایش پنل نوع
# ================================
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

    # محدودیت گروه
    if update.effective_chat.type != "private":
        allowed = await is_admin(update, context)
        if not allowed:
            return

    pending_links[update.effective_chat.id] = url

    keyboard = [
        [InlineKeyboardButton("🎵 Audio (MP3)", callback_data="yt_audio")],
        [InlineKeyboardButton("🎬 Video (MP4)", callback_data="yt_video")],
    ]
    await update.message.reply_text(
        "🎬 لطفاً نوع ارسال را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================================
# مرحله ۲ — ارسال مستقیم با کش
# ================================
async def youtube_quality_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    chat_id = cq.message.chat_id
    await cq.answer()

    if update.effective_chat.type != "private":
        allowed = await is_admin(update, context)
        if not allowed:
            return

    url = pending_links.get(chat_id)
    if not url:
        return await cq.edit_message_text("❌ لینک معتبر یافت نشد.")

    choice = cq.data  # yt_audio یا yt_video

    if str(chat_id) not in YT_CACHE:
        YT_CACHE[str(chat_id)] = {}

    cache_key = f"{url}_{choice}"
    if cache_key in YT_CACHE[str(chat_id)]:
        cached = YT_CACHE[str(chat_id)][cache_key]
        if choice == "yt_audio":
            await cq.edit_message_text("🎵 ارسال صوت از کش ...")
            await context.bot.send_audio(
                chat_id,
                cached["direct_url"],
                caption=f"🎵 {cached.get('title','Audio')}",
                reply_markup=get_add_btn(update.effective_chat.type)
            )
        else:
            await cq.edit_message_text("🎬 ارسال ویدیو از کش ...")
            await context.bot.send_video(
                chat_id,
                cached["direct_url"],
                caption=f"🎬 {cached.get('title','YouTube Video')}",
                reply_markup=get_add_btn(update.effective_chat.type)
            )
        return

    # استخراج لینک مستقیم در executor
    loop = asyncio.get_running_loop()
    info, direct_url = await loop.run_in_executor(executor, _get_direct_link, url, "audio" if choice=="yt_audio" else "video")

    if choice == "yt_audio":
        sent = await context.bot.send_audio(
            chat_id,
            direct_url,
            caption=f"🎵 {info.get('title','Audio')}",
            reply_markup=get_add_btn(update.effective_chat.type)
        )
    else:
        sent = await context.bot.send_video(
            chat_id,
            direct_url,
            caption=f"🎬 {info.get('title','YouTube Video')}",
            reply_markup=get_add_btn(update.effective_chat.type)
        )

    # ذخیره در کش
    YT_CACHE[str(chat_id)][cache_key] = {
        "direct_url": direct_url,
        "title": info.get("title",""),
        "type": "audio" if choice=="yt_audio" else "video"
    }
    save_yt_cache()
