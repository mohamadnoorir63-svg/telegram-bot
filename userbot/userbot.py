# userbot/userbot.py
from telethon import TelegramClient, events, errors
from telethon.sessions import StringSession
import os, asyncio

async def start_userbot():
    """⚙️ اجرای یوزربات در کنار ربات اصلی"""
    print("🔌 در حال اتصال userbot ...")

    api_id = int(os.getenv("API_ID", "0"))
    api_hash = os.getenv("API_HASH", "")
    session_string = os.getenv("SESSION_STRING", "")

    if not api_id or not api_hash:
        print("🚫 API_ID یا API_HASH تنظیم نشده — یوزربات غیرفعال ماند.")
        return

    try:
        # ساخت یا بارگذاری سشن
        if not session_string:
            if os.path.exists("userbot.session"):
                print("📂 SESSION_STRING پیدا نشد — در حال خواندن از فایل userbot.session ...")
                client = TelegramClient("userbot.session", api_id, api_hash)
            else:
                print("⚠️ نه SESSION_STRING هست، نه userbot.session — یوزربات اجرا نمی‌شود.")
                return
        else:
            client = TelegramClient(StringSession(session_string), api_id, api_hash)

        await client.start()
        me = await client.get_me()
        print(f"✅ Userbot آنلاین شد ({me.first_name}) [ID: {me.id}]")

        # 📡 تست آنلاین بودن
        @client.on(events.NewMessage(pattern=r"^\.ping$"))
        async def ping_handler(event):
            await event.reply("🏓 Userbot فعاله ✅")

        # 💣 پاکسازی سریع (nuke)
        @client.on(events.NewMessage(pattern=r"^\.nuke(?:\s+(\d+))?$"))
        async def nuke_handler(event):
            limit = int(event.pattern_match.group(1) or 5000)
            msg = await event.reply("🧹 در حال پاکسازی...")
            try:
                msgs = await client.get_messages(event.chat_id, limit=limit)
                ids = [m.id for m in msgs]
                for i in range(0, len(ids), 100):
                    await client.delete_messages(event.chat_id, ids[i:i+100], revoke=True)
                    await asyncio.sleep(0.25)
                await msg.edit(f"✅ پاکسازی کامل شد ({len(ids)} پیام)")
            except Exception as e:
                await msg.edit(f"❌ خطا در پاکسازی: {e}")

        await client.run_until_disconnected()

    except Exception as e:
        print(f"❌ خطا در userbot: {e}")
