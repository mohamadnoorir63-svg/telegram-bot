from telethon import TelegramClient, events
from telethon.sessions import StringSession
import asyncio
import requests

# -------------------------
#  API ID / HASH
# -------------------------
API_ID = 32796779
API_HASH = "4deabef1568103b3242db6f74a73e8a5"

# -------------------------
#  SESSION STRING واقعی
# -------------------------
SESSION_STRING = "1ApWapzMBuzET2YvEj_TeHnWFPVKUV1Wbqb3o534-WL_U0fbXd-RTUWuML8pK60sh9B_oGsE3T3RQjIhXWs4tM30UPr3BFxpF6EUCB9BSPGCtmienHmXHI9k-zT7iI6HZLtqlNeGi0zMxAA8hUY25V1IhKgnujyHWcUA9VfVXNmJTtq54cZgdvTSa3EntYNmTlMcsaX7p82yoSKpz3LL5SB9ZL35PZCVAVXMIcfBbv_Ofr6w9CA4yBcMm9-t4NjRRLaZnwH-rU29RmtM8qM3n-K7mvCFRfQ1Vmw_HBFcYJlx-mHN_rxgo55XIC3Y3_9XoQ9f0FypxXgxEsYUjH5LosGP2KA_tMZo="

client2 = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# -------------------------
#  Handler برای ping
# -------------------------
@client2.on(events.NewMessage(pattern="ping"))
async def ping_handler(event):
    await event.reply("🏓 Pong! یوزربات دوم فعال است.")


# -------------------------
#  دریافت موزیک از SoundCloud
# -------------------------
def search_soundcloud(query):
    url = f"https://api-v2.soundcloud.com/search/tracks?q={query}&client_id=VptP8XS8eYUxk5nYVx20xUDxg6dSPl1U&limit=1"

    r = requests.get(url)
    if r.status_code != 200:
        return None

    data = r.json()
    if "collection" not in data or len(data["collection"]) == 0:
        return None

    track = data["collection"][0]

    return {
        "title": track.get("title"),
        "author": track.get("user", {}).get("username"),
        "track_url": track.get("permalink_url"),
        "stream_url": track.get("media", {}).get("transcodings", [])[0].get("url") if track.get("media") else None
    }


# -------------------------
#  Handler برای جستجو موزیک
# -------------------------
@client2.on(events.NewMessage)
async def music_handler(event):
    text = event.message.text.strip()

    if text.lower() == "ping":
        return

    await event.reply(f"🎧 در حال جستجوی آهنگ: {text}")

    result = search_soundcloud(text)

    if not result:
        await event.reply("❌ هیچ موزیکی پیدا نشد.")
        return

    # اگر استریم مستقیم دارد
    stream_link = None
    if result["stream_url"]:
        # گرفتن لینک قابل پخش (قانونی)
        stream_res = requests.get(result["stream_url"], params={"client_id": "VptP8XS8eYUxk5nYVx20xUDxg6dSPl1U"})
        if stream_res.status_code == 200:
            stream_link = stream_res.json().get("url")

    msg = f"""
🎵 <b>{result['title']}</b>
👤 <i>{result['author']}</i>

📎 لینک رسمی:
{result['track_url']}

🎧 لینک پخش مستقیم:
{stream_link if stream_link else "❌ موجود نیست"}
"""

    await event.reply(msg, parse_mode="html")


# -------------------------
#  اجرای یوزربات
# -------------------------
async def start_userbot2():
    print("⚡ یوزربات دوم فعال شد...")
    await client2.start()
    await client2.run_until_disconnected()


if __name__ == "__main__":
    try:
        asyncio.run(start_userbot2())
    except Exception as e:
        print(f"❌ خطا: {e}")
