import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from youtube_search import YoutubeSearch
import os
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, APIC


# ---------- سرچ موزیک ----------
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
    text = "🎵 موزیک‌های پیدا شده:\n\n"

    for i, item in enumerate(results):
        title = item["title"]
        video_id = item["id"]
        duration = item["duration"]
        channel = item["channel"]

        text += f"{i+1}. {title} — {channel} ({duration})\n"

        keyboard.append([InlineKeyboardButton(title, callback_data=f"music_select:{video_id}")])

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


# ---------- گرفتن لینک صوتی از Piped ----------
def get_piped_audio(video_id):
    try:
        api = f"https://piped.video/streams/{video_id}"
        data = requests.get(api).json()

        audio_streams = data.get("audioStreams", [])
        if not audio_streams:
            return None, None

        # پیدا کردن کیفیت 320
        best_audio = None
        for stream in audio_streams:
            if "bitrate" in stream and stream["bitrate"] == 320:
                best_audio = stream
                break

        # اگر 320 نبود، بهترین کیفیت
        if not best_audio:
            best_audio = audio_streams[0]

        return best_audio["url"], data.get("thumbnailUrl")

    except:
        return None, None


# ---------- دانلود موزیک ----------
def download_audio(video_id):
    audio_url, cover_url = get_piped_audio(video_id)
    if not audio_url:
        return None

    filename = f"{video_id}.mp3"

    r = requests.get(audio_url, stream=True)
    with open(filename, "wb") as f:
        for chunk in r.iter_content(chunk_size=2048):
            if chunk:
                f.write(chunk)

    return filename, cover_url


# ---------- اضافه کردن عنوان، خواننده، کاور ----------
def tag_mp3(file_path, title, artist, cover_url):
    try:
        audio = MP3(file_path, ID3=ID3)

        try:
            audio.add_tags()
        except:
            pass

        audio.tags["TIT2"] = TIT2(encoding=3, text=title)
        audio.tags["TPE1"] = TPE1(encoding=3, text=artist)

        if cover_url:
            cover_data = requests.get(cover_url).content
            audio.tags["APIC"] = APIC(
                encoding=3,
                mime="image/jpeg",
                type=3,
                desc="Cover",
                data=cover_data
            )

        audio.save()
    except:
        pass


# ---------- انتخاب موزیک ----------
async def music_select_handler(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    video_id = query.data.split(":")[1]
    await query.edit_message_text("⬇ در حال دانلود موزیک... لطفاً صبر کنید...")

    filepath, cover_url = download_audio(video_id)

    if not filepath:
        await query.edit_message_text("❌ خطا در دانلود موزیک!")
        return

    # استخراج عنوان آهنگ از YouTubeSearch (بهترین روش موجود)
    search = YoutubeSearch(video_id, max_results=1).to_dict()
    title = search[0]["title"] if search else "Music"
    artist = search[0]["channel"] if search else "Unknown Artist"

    # اضافه کردن عنوان و کاور
    tag_mp3(filepath, title, artist, cover_url)

    try:
        await query.message.reply_audio(
            audio=open(filepath, "rb"),
            title=title,
            performer=artist,
        )
    except:
        await query.edit_message_text("❌ خطا در ارسال فایل!")

    try:
        os.remove(filepath)
    except:
        pass
