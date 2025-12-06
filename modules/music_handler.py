# modules/soundcloud_handler.py
import os
import requests
import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# ----------------------------------
# Client ID عمومی SoundCloud
# ----------------------------------
CLIENT_ID = "2t9loNQH90kzJcsFCODdigxfp325aq4z"  # نسخه عمومی که اکثر منابع استفاده می‌کنند

# ----------------------------------
# تبدیل URL Stream به MP3
# ----------------------------------
async def download_soundcloud(url: str, title: str) -> str:
    mp3_path = os.path.join(DOWNLOAD_FOLDER, f"{title}.mp3")
    try:
        r = requests.get(url, stream=True)
        with open(mp3_path, "wb") as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
        return mp3_path
    except Exception as e:
        print(f"❌ خطا در دانلود: {e}")
        return None

# ----------------------------------
# جستجوی موزیک در SoundCloud
# ----------------------------------
async def music_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    query = update.message.text.replace("/موزیک", "").strip()
    if not query:
        await update.message.reply_text("لطفاً نام آهنگ یا خواننده را وارد کنید.")
        return

    msg = await update.message.reply_text("🔍 در حال جستجوی موزیک در SoundCloud...")

    search_url = f"https://api-v2.soundcloud.com/search/tracks?q={query}&client_id={CLIENT_ID}&limit=5"
    try:
        res = requests.get(search_url, timeout=10).json()
        tracks = res.get("collection")
        if not tracks:
            await msg.edit_text("❌ موزیکی پیدا نشد.")
            return

        buttons = []
        for i, track in enumerate(tracks, start=1):
            title = track.get("title")
            track_id = track.get("id")
            buttons.append([InlineKeyboardButton(f"{i}. {title}", callback_data=f"music_select:{track_id}")])

        await msg.edit_text("⬇️ یکی از گزینه‌ها را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(buttons))

    except Exception as e:
        await msg.edit_text(f"❌ خطا در جستجوی موزیک: {e}")

# ----------------------------------
# هندلر انتخاب موزیک
# ----------------------------------
async def music_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    track_id = query.data.split(":")[1]

    # دریافت اطلاعات کامل آهنگ
    track_url = f"https://api-v2.soundcloud.com/tracks/{track_id}?client_id={CLIENT_ID}"
    try:
        track_info = requests.get(track_url, timeout=10).json()
        title = track_info.get("title")
        stream_url = f"{track_info.get('media')['transcodings'][0]['url']}?client_id={CLIENT_ID}"

        msg = await query.edit_message_text("⬇️ در حال دانلود موزیک... لطفاً صبر کنید...")

        # دریافت لینک واقعی mp3
        stream_res = requests.get(stream_url, timeout=10).json()
        mp3_download_url = stream_res.get("url")

        mp3_path = await download_soundcloud(mp3_download_url, title)
        if mp3_path and os.path.exists(mp3_path):
            await context.bot.send_audio(chat_id=query.message.chat.id, audio=open(mp3_path, "rb"), title=title)
            os.remove(mp3_path)
            await msg.delete()
        else:
            await msg.edit_text("❌ خطا در دانلود موزیک.")

    except Exception as e:
        await query.edit_message_text(f"❌ خطا در پردازش موزیک: {e}")
