from telethon import TelegramClient, events
from telethon.sessions import StringSession
import asyncio
import re
from telethon.errors import InviteHashExpiredError, InviteHashInvalidError

API_ID = 32796779
API_HASH = "4deabef1568103b3242db6f74a73e8a5"
SESSION_STRING = "1ApWapzMBuzET2YvEj_TeHnWFPVKUV1Wbqb3o534-WL_U0fbXd-RTUWuML8pK60sh9B_oGsE3T3RQjIhXWs4tM30UPr3BFxpF6EUCB9BSPGCtmienHmXHI9k-zT7iI6HZLtqlNeGi0zMxAA8hUY25V1IhKgnujyHWcUA9VfVXNmJTtq54cZgdvTSa3EntYNmTlMcsaX7p82yoSKpz3LL5SB9ZL35PZCVAVXMIcfBbv_Ofr6w9CA4yBcMm9-t4NjRRLaZnwH-rU29RmtM8qM3n-K7mvCFRfQ1Vmw_HBFcYJlx-mHN_rxgo55XIC3Y3_9XoQ9f0FypxXgxEsYUjH5LosGP2KA_tMZo="

client2 = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# الگوهای لینک‌ گروه
invite_pattern = r"(https?://t\.me/[\w\d_\-+/=]+)"

@client2.on(events.NewMessage)
async def join_group_handler(event):
    text = event.raw_text

    # بررسی لینک دعوت
    match = re.search(invite_pattern, text)
    if not match:
        return

    invite_link = match.group(1)

    await event.reply("🔍 در حال تلاش برای پیوستن...")

    try:
        await client2(JoinChannelRequest(invite_link))
        await event.reply("✅ با موفقیت به گروه پیوستم!")

    except InviteHashExpiredError:
        await event.reply("❌ لینک دعوت منقضی شده است.")
    except InviteHashInvalidError:
        await event.reply("❌ لینک دعوت معتبر نیست.")
    except Exception as e:
        await event.reply(f"⚠️ خطا در پیوستن:\n{e}")

async def start_userbot2():
    print("⚡ Userbot2 Ready!")
    await client2.start()
    await client2.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(start_userbot2())
