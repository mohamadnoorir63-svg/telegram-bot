import os
import shutil
import subprocess
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
RESULTS_PER_PAGE = 5  # تعداد نتایج در هر صفحه

async def convert_to_mp3(video_path: str) -> str:
    """تبدیل ویدیو/آهنگ به MP3"""
    mp3_path = video_path.rsplit(".", 1)[0] + ".mp3"
    if not shutil.which("ffmpeg"):
        return None
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-ab", "192k", "-ar", "44100",
        "-f", "mp3", mp3_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return mp3_path

async def soundcloud_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """جستجو موزیک در SoundCloud و نمایش نتایج صفحه‌بندی"""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    chat_id = update.effective_chat.id

    if not text.startswith("آهنگ "):
        return

    query = text.replace("آهنگ ", "", 1).strip()
    if not query:
        await update.message.reply_text("❌ لطفاً نام آهنگ را وارد کنید.")
        return

    msg = await update.message.reply_text("🔍 در حال جستجو در SoundCloud...")

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        "extract_flat": True,  # فقط اطلاعات، دانلود نمی‌کنه
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"scsearch:{query}", download=False)

        if not info or "entries" not in info or not info["entries"]:
            await msg.edit_text("❌ آهنگ پیدا نشد.")
            return

        # ذخیره نتایج در context برای صفحه‌بندی
        context.user_data["sc_results"] = info["entries"]
        context.user_data["sc_page"] = 0

        await _send_results_page(update, context, msg)

    except Exception as e:
        await msg.edit_text(f"❌ خطا در جستجوی موزیک:\n{e}")


async def _send_results_page(update: Update, context: ContextTypes.DEFAULT_TYPE, msg=None):
    """ارسال صفحه مشخصی از نتایج"""
    page = context.user_data.get("sc_page", 0)
    entries = context.user_data.get("sc_results", [])
    start = page * RESULTS_PER_PAGE
    end = start + RESULTS_PER_PAGE
    current_entries = entries[start:end]

    keyboard = []
    for i, track in enumerate(current_entries, start=1):
        title = track.get("title", "SoundCloud")
        track_id = track.get("id")
        keyboard.append([InlineKeyboardButton(f"{start+i}. {title}", callback_data=f"music_select:{track_id}")])

    nav_buttons = []
    if start > 0:
        nav_buttons.append(InlineKeyboardButton("⏮️ قبلی", callback_data="music_page_prev"))
    if end < len(entries):
        nav_buttons.append(InlineKeyboardButton("⏭️ بعدی", callback_data="music_page_next"))

    if nav_buttons:
        keyboard.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)

    if msg:
        await msg.edit_text("🎵 یکی از آهنگ‌ها را انتخاب کنید:", reply_markup=reply_markup)
    else:
        await update.callback_query.message.edit_text("🎵 یکی از آهنگ‌ها را انتخاب کنید:", reply_markup=reply_markup)


async def music_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دانلود آهنگ انتخابی"""
    query = update.callback_query
    await query.answer()

    if query.data.startswith("music_select:"):
        track_id = query.data.split(":")[1]

        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "noplaylist": True,
            "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
        }

        msg = await query.message.edit_text("⬇️ در حال دانلود آهنگ... لطفاً صبر کنید...")

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"https://soundcloud.com/i/tracks/{track_id}", download=True)
                filename = ydl.prepare_filename(info)

            mp3_path = await convert_to_mp3(filename)
            if mp3_path and os.path.exists(mp3_path):
                await query.message.reply_audio(mp3_path, caption=f"🎵 {info.get('title','SoundCloud')}")
                os.remove(mp3_path)
            else:
                await query.message.reply_document(filename, caption=f"🎵 {info.get('title','SoundCloud')}")

            if os.path.exists(filename):
                os.remove(filename)

            await msg.delete()
        except Exception as e:
            await msg.edit_text(f"❌ خطا در دانلود موزیک:\n{e}")

    # صفحه بعدی/قبلی
    elif query.data == "music_page_next":
        context.user_data["sc_page"] += 1
        await _send_results_page(update, context)
    elif query.data == "music_page_prev":
        context.user_data["sc_page"] -= 1
        await _send_results_page(update, context)
