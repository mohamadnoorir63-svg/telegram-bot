# -- coding: utf-8 --
import os
import telebot
import requests

# 🔐 گرفتن مقادیر از تنظیمات Heroku
BOT_TOKEN = os.getenv("BOT_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# 🌐 لینک APIهای RapidAPI
YOUTUBE_SEARCH_URL = "https://youtube-v31.p.rapidapi.com/search"
YOUTUBE_DOWNLOAD_URL = "https://youtube-mp36.p.rapidapi.com/dl"

# 🎬 فرمان شروع
@bot.message_handler(commands=["start"])
def start(m):
    txt = (
        "🎵 <b>سلام!</b>\n"
        "به ربات جستجوگر و دانلود موزیک خوش اومدی 🎧\n\n"
        "کافیه اسم آهنگ یا لینک یوتیوب رو بفرستی تا برات بیارم 🎶\n\n"
        "مثلاً:\n"
        "<code>شادمهر خسته شدم</code>\n"
        "یا:\n"
        "<code>https://www.youtube.com/watch?v=6f3jKxCQEzo</code>\n\n"
        "✨ پشتیبانی از فارسی و انگلیسی ✅"
    )
    bot.send_message(m.chat.id, txt)

# 🎶 هندل هر پیام متنی (جستجو یا لینک)
@bot.message_handler(func=lambda m: True)
def handle_message(m):
    query = m.text.strip()

    if "youtube.com" in query or "youtu.be" in query:
        download_from_youtube(m, query)
    else:
        search_and_download(m, query)

# 🔎 جستجوی یوتیوب با نام آهنگ
def search_and_download(m, query):
    bot.send_message(m.chat.id, f"🔍 در حال جست‌وجوی آهنگ <b>{query}</b> ... لطفاً صبر کنید ⏳")

    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "youtube-v31.p.rapidapi.com"
    }
    params = {"q": query, "part": "snippet", "maxResults": "1"}

    try:
        r = requests.get(YOUTUBE_SEARCH_URL, headers=headers, params=params, timeout=10)
        data = r.json()

        video_id = data["items"][0]["id"]["videoId"]
        title = data["items"][0]["snippet"]["title"]
        channel = data["items"][0]["snippet"]["channelTitle"]
        thumb = data["items"][0]["snippet"]["thumbnails"]["high"]["url"]

        youtube_url = f"https://www.youtube.com/watch?v={video_id}"
        caption = f"🎵 <b>{title}</b>\n👤 {channel}\n\n⏬ در حال آماده‌سازی آهنگ..."
        bot.send_photo(m.chat.id, thumb, caption=caption)

        download_from_youtube(m, youtube_url)

    except Exception as e:
        bot.send_message(m.chat.id, "❌ خطایی در جست‌وجوی آهنگ رخ داد.\nلطفاً دوباره تلاش کن 🎶")

# ⬇️ دانلود آهنگ از یوتیوب
def download_from_youtube(m, url):
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "youtube-mp36.p.rapidapi.com"
    }
    params = {"url": url}

    try:
        r = requests.get(YOUTUBE_DOWNLOAD_URL, headers=headers, params=params, timeout=15)
        data = r.json()

        if "link" in data:
            audio_url = data["link"]
            title = data.get("title", "Music")
            caption = f"✅ <b>{title}</b>\n\n🎧 آهنگ آماده است!\n🔗 <a href='{audio_url}'>دانلود مستقیم</a>"
            bot.send_message(m.chat.id, caption)
        else:
            bot.send_message(m.chat.id, "❗ آهنگ پیدا نشد یا خطایی رخ داد.")

    except Exception as e:
        bot.send_message(m.chat.id, "⚠️ خطا در ارتباط با سرور.\nلطفاً دوباره تلاش کن.")

print("✅ Bot is running...")
bot.infinity_polling()
