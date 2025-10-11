# -- coding: utf-8 --
import os
import telebot
from yt_dlp import YoutubeDL

# گرفتن اطلاعات از Environment (هاست Heroku)
TOKEN = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

def download_audio(query):
    """دانلود آهنگ از یوتیوب به صورت mp3 با کاور"""
    try:
        opts = {
            "format": "bestaudio/best",
            "noplaylist": True,
            "outtmpl": "song.%(ext)s",
            "quiet": True,
            "default_search": "ytsearch1",
            "writethumbnail": True,  # دانلود تصویر کاور
            "postprocessors": [
                {  # تبدیل به mp3
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "128",
                },
                {  # تنظیم تصویر کاور برای آهنگ
                    "key": "EmbedThumbnail",
                },
            ],
        }

        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(query, download=True)
            title = info.get("title", "Music")
            artist = info.get("uploader", "Unknown Artist")
            thumb = info.get("thumbnail")
        return "song.mp3", title, artist, thumb
    except Exception as e:
        print("Error:", e)
        return None, None, None, None

# هندل پیام‌ها
@bot.message_handler(func=lambda m: True)
def handle_message(m):
    query = m.text.strip()
    bot.reply_to(m, f"🎶 در حال جستجوی آهنگ: {query} ... لطفاً صبر کنید ⏳")
    path, title, artist, thumb = download_audio(query)
    if not path:
        return bot.send_message(m.chat.id, "❗ خطا در دانلود آهنگ یا نتیجه‌ای یافت نشد.")
    caption = f"🎵 <b>{title}</b>\n👤 <i>{artist}</i>"
    if thumb:
        bot.send_photo(m.chat.id, thumb, caption=caption)
    bot.send_audio(m.chat.id, open(path, "rb"), title=title, performer=artist, caption=caption)
    os.remove(path)

print("✅ Music Bot is Running...")
bot.infinity_polling()
