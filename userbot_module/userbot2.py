from telethon import TelegramClient
from telethon.sessions import StringSession
import asyncio

# 🔹 API_ID و API_HASH همان اکانت دوم
API_ID = 32796779
API_HASH = "4deabef1568103b3242db6f74a73e8a5"

# 🔹 SESSION_STRING واقعی که گرفتیم
SESSION_STRING = "1ApWapzMBuzET2YvEj_TeHnWFPVKUV1Wbqb3o534-WL_U0fbXd-RTUWuML8pK60sh9B_oGsE3T3RQjIhXWs4tM30UPr3BFxpF6EUCB9BSPGCtmienHmXHI9k-zT7iI6HZLtqlNeGi0zMxAA8hUY25V1IhKgnujyHWcUA9VfVXNmJTtq54cZgdvTSa3EntYNmTlMcsaX7p82yoSKpz3LL5SB9ZL35PZCVAVXMIcfBbv_Ofr6w9CA4yBcMm9-t4NjRRLaZnwH-rU29RmtM8qM3n-K7mvCFRfQ1Vmw_HBFcYJlx-mHN_rxgo55XIC3Y3_9XoQ9f0FypxXgxEsYUjH5LosGP2KA_tMZo="

# ایجاد Client با StringSession
client2 = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

async def start_userbot2():
    print("⚡ یوزربات دوم در حال اجراست...")
    await client2.start()
    await client2.run_until_disconnected()

# اجرا مستقیم
if __name__ == "__main__":
    try:
        asyncio.run(start_userbot2())
    except Exception as e:
        print(f"❌ خطا در اجرای یوزربات دوم: {e}")
