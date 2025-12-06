# modules/music_handler.py
import requests
import os
import uuid
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CallbackQueryHandler

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# جایگزین با Client ID خودت از Jamendo
JAMENDO_CLIENT_ID = "YOUR_JAMENDO_CLIENT_ID"

# -----------------------------
# جستجوی موزیک
# -----------------------------
async def music_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """جستجوی موزیک با Jamendo API"""
    if not update.message or not update.message.text:
        return

    query = update.message.text.replace("/موزیک", "").strip()
    if not query:
        await update.message.reply_text("❌ لطفاً نام آهنگ یا خواننده را وارد کنید.")
        return

    msg = await update.message.reply_text("🔍 در حال جستجو...")

    url = f"https://api.jamendo.com/v3.0/tracks/?client_id={JAMENDO_CLIENT_ID}&format=json&limit=5&search={query}"
    try:
        resp = requests.get(url, timeout=10).json()
        results = resp.get("results", [])

        if not results:
            await msg.edit_text("❌ نتیجه‌ای پیدا نشد.")
            return

        # ساخت دکمه‌های انتخاب آهنگ
        buttons = []
        for track in results:
            track_id = track["id"]
            title = track["name"]
            artist = track["artist_name"]
            buttons.append(
                [InlineKeyboardButton(f"{title} - {artist}", callback_data=f"music_select:{track_id}")]
            )

        await msg.edit_text(
            "🎵 نتایج پیدا شده:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    except Exception as e:
        await msg.edit_text(f"❌ خطا در جستجوی موزیک: {e}")


# -----------------------------
# دانلود و ارسال موزیک انتخابی
# -----------------------------
async def music_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دانلود و ارسال آهنگ انتخابی"""
    query = update.callback_query
    await query.answer()

    track_id = query.data.split(":")[1]
    msg = await query.edit_message_text("⬇ در حال دانلود موزیک... لطفاً صبر کنید...")

    url = f"https://api.jamendo.com/v3.0/tracks/?client_id={JAMENDO_CLIENT_ID}&format=json&id={track_id}"
    try:
        resp = requests.get(url, timeout=10).json()
        track = resp["results"][0]
        mp3_url = track["audio"]
        title = track["name"]
        artist = track["artist_name"]

        # دانلود فایل
        filename = os.path.join(DOWNLOAD_FOLDER, f"{uuid.uuid4().hex}.mp3")
        with requests.get(mp3_url, stream=True) as r:
            r.raise_for_status()
            with open(filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        # ارسال به تلگرام
        await context.bot.send_audio(
            chat_id=query.message.chat.id,
            audio=open(filename, "rb"),
            caption=f"🎵 {title} - {artist}"
        )

        os.remove(filename)
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود موزیک: {e}")
