import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from youtube_search import YoutubeSearch
import os


# ---------- جستجوی موزیک ----------
async def music_search_handler(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.replace("/موزیک", "").strip()

    if not query:
        await update.message.reply_text("❗ نام آهنگ را بعد از /موزیک بنویس\nمثال:\n/موزیک مهرداد جم شیک")
        return

    await update.message.reply_text("🔍 در حال جستجو...")

    results = YoutubeSearch(query, max_results=5).to_dict()

    if not results:
        await update.message.reply_text("❌ هیچ موزیکی پیدا نشد!")
        return

    keyboard = []
    for item in results:
        title = item["title"]
        video_id = item["id"]

        keyboard.append([InlineKeyboardButton(title, callback_data=f"music_select:{video_id}")])

    await update.message.reply_text(
        "🎵 موزیک مورد نظر را انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ---------- گرفتن لینک بدون کوکی ----------
def get_audio_url(video_id):
    try:
        api = f"https://piped.video/streams/{video_id}"
        r = requests.get(api).json()
        audio_streams = r.get("audioStreams", [])

        if not audio_streams:
            return None

        return audio_streams[0]["url"]

    except:
        return None


# ---------- دانلود موزیک ----------
def download_audio(video_id):
    audio_url = get_audio_url(video_id)
    if not audio_url:
        return None

    filename = f"{video_id}.mp3"

    r = requests.get(audio_url, stream=True)
    with open(filename, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

    return filename


# ---------- انتخاب موزیک ----------
async def music_select_handler(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    video_id = query.data.split(":")[1]

    await query.edit_message_text("⬇ در حال دانلود موزیک...")

    filepath = download_audio(video_id)

    if not filepath:
        await query.edit_message_text("❌ خطا در دانلود موزیک!")
        return

    try:
        await query.message.reply_audio(open(filepath, "rb"))
    except:
        await query.edit_message_text("❌ خطا در ارسال فایل!")

    # حذف فایل بعد ارسال
    try:
        os.remove(filepath)
    except:
        pass
