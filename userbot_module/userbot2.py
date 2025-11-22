from telethon import TelegramClient
from telethon.sessions import StringSession
import asyncio

# 🔹 API_ID و API_HASH همان اکانت دوم
API_ID = 32796779
API_HASH = "4deabef1568103b3242db6f74a73e8a5"

# 🔹 SESSION_STRING2 که ساختی
SESSION_STRING = "SESSION_STRING2"  # ← این رشته بزرگ را دقیقاً اینجا بذار

# ایجاد Client با StringSession
client2 = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

async def start_userbot2():
    print("⚡ یوزربات دوم در حال اجراست...")
    await client2.start()
    await client2.run_until_disconnected()

# برای اجرا به صورت مستقیم
if __name__ == "__main__":
    try:
        asyncio.run(start_userbot2())
    except Exception as e:
        print(f"❌ خطا در اجرای یوزربات دوم: {e}")
