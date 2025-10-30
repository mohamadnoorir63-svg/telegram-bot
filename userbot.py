# ==========================================================
# 🤖 Userbot System — Telethon Integration
# ==========================================================
import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# 🧩 اتصال مستقیم به سیستم کنترل گروه
from group_control.group_control import lock_via_userbot, unlock_via_userbot, get_group_status

# ==========================================================
# ⚙️ دریافت تنظیمات از متغیرهای محیطی (Heroku Config Vars)
# ==========================================================
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION_STRING = os.getenv("SESSION_STRING", "")

# ==========================================================
# 🚀 راه‌اندازی کلاینت
# ==========================================================
async def start_userbot():
    if not API_ID or not API_HASH:
        print("⚠️ API_ID یا API_HASH تنظیم نشده. یوزربات نمی‌تواند اجرا شود.")
        return

    # اگر SESSION_STRING نبود، از فایل session استفاده کن
    if not SESSION_STRING:
        if os.path.exists("userbot.session"):
            print("📂 SESSION_STRING پیدا نشد، دارم از فایل userbot.session استفاده می‌کنم...")
            client = TelegramClient("userbot.session", API_ID, API_HASH)
        else:
            print("⚠️ نه SESSION_STRING هست نه userbot.session — یوزربات خاموش می‌ماند.")
            return
    else:
        client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

    await client.start()
    me = await client.get_me()
    print(f"✅ Userbot آنلاین شد ({me.first_name}) [ID: {me.id}]")

    # ==========================================================
    # 📡 دستورات مخصوص یوزربات
    # ==========================================================

    # دستور تست ساده
    @client.on(events.NewMessage(pattern=r"^\.ping$"))
    async def ping(event):
        await event.reply("🏓 Userbot فعاله ✅")

    # قفل کردن
    @client.on(events.NewMessage(pattern=r"^\.قفل (.+)$"))
    async def lock_from_userbot(event):
        key = event.pattern_match.group(1).strip().lower()
        lock_via_userbot(event.chat_id, key)
        await event.reply(f"🔒 قفل <b>{key}</b> فعال شد (از طریق یوزربات)", parse_mode="html")

    # باز کردن
    @client.on(events.NewMessage(pattern=r"^\.باز (.+)$"))
    async def unlock_from_userbot(event):
        key = event.pattern_match.group(1).strip().lower()
        unlock_via_userbot(event.chat_id, key)
        await event.reply(f"🔓 قفل <b>{key}</b> باز شد (از طریق یوزربات)", parse_mode="html")

    # وضعیت قفل‌ها
    @client.on(events.NewMessage(pattern=r"^\.وضعیت$"))
    async def status_from_userbot(event):
        locks = get_group_status(event.chat_id)
        if not locks:
            return await event.reply("🔓 هیچ قفلی فعال نیست.")
        text = "🧱 <b>وضعیت قفل‌های گروه:</b>\n\n" + "\n".join(
            f"▫️ {k}: {'🔒' if v else '🔓'}" for k, v in locks.items()
        )
        await event.reply(text, parse_mode="html")

    # اجرای دائم
    await client.run_until_disconnected()


# ==========================================================
# 🔁 اجرای Async Loop
# ==========================================================
if __name__ == "__main__":
    try:
        asyncio.run(start_userbot())
    except KeyboardInterrupt:
        print("⛔ Userbot متوقف شد.")
