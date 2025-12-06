import os
import asyncio
import aiohttp
from telethon import TelegramClient, events, sessions

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH"))
SESSION_STRING = os.environ.get("SESSION_STRING")
CLIENT_ID = os.environ.get("JAMENDO_CLIENT_ID")  # Jamendo client_id

client = TelegramClient(sessions.StringSession(SESSION_STRING), API_ID, API_HASH)

# ---------- دانلود موزیک از Jamendo ----------
async def fetch_jamendo_track(query):
    url = (
        "https://api.jamendo.com/v3.0/tracks"
        f"?client_id={CLIENT_ID}"
        f"&format=json"
        f"&limit=1"
        f"&namesearch={aiohttp.helpers.quote(query)}"
        f"&audiodownload_allowed=true"
    )
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            results = data.get("results", [])
            if not results:
                return None
            track = results[0]
            return track.get("audiodownload")

# ---------- فرمان موزیک ----------
@client.on(events.NewMessage(pattern=r"^/music (.+)"))
async def music_command(event):
    query = event.pattern_match.group(1).strip()
    chat_id = event.chat_id
    msg = await client.send_message(chat_id, f"🔍 در حال جستجو برای: {query}")
    try:
        dl_url = await fetch_jamendo_track(query)
        if not dl_url:
            return await msg.edit("⚠️ آهنگی با این نام پیدا نشد یا دانلود آن مجاز نیست.")
        async with aiohttp.ClientSession() as session:
            async with session.get(dl_url) as resp:
                content = await resp.read()
        file_name = f"downloads/{query}.mp3"
        os.makedirs("downloads", exist_ok=True)
        with open(file_name, "wb") as f:
            f.write(content)
        await client.send_file(chat_id, file_name, caption=f"🎶 {query}")
        os.remove(file_name)
        await msg.delete()
    except Exception as e:
        await msg.edit(f"❌ خطا در دانلود موزیک: {e}")

# ---------- فانکشن استارت یوزربات ----------
async def start_userbot():
    await client.start()
    print("✅ Userbot ready and listening...")
    await client.run_until_disconnected()

# ---------- اجرا مستقیم ----------
if __name__ == "__main__":
    asyncio.run(start_userbot())
