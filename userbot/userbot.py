# ==========================================================
# 🇮🇷 Userbot فارسی – نسخه‌ی مستقل و ایمن
# ==========================================================
# نیاز به:
#  ┣ TELETHON
#  ┣ متغیرهای محیطی: API_ID, API_HASH, SESSION_STRING
# ==========================================================

from telethon import TelegramClient, events, errors
from telethon.sessions import StringSession
import os, asyncio

print("🚀 در حال راه‌اندازی یوزربات ...")

# ---- تنظیمات اتصال ----
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION = os.getenv("SESSION_STRING", "")  # یا فایل userbot.session

OWNER_ID = int(os.getenv("ADMIN_ID", "7089376754"))  # آیدی خودت
BATCH_SIZE = 100
SLEEP_BETWEEN = 0.35

# ---- اتصال ----
if not API_ID or not API_HASH:
    raise SystemExit("🚫 API_ID یا API_HASH تنظیم نشده است!")

client = TelegramClient(StringSession(SESSION) if SESSION else "userbot.session", API_ID, API_HASH)

# ---- کمک‌کننده ----
def chunked(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

# ==========================================================
# 🔸 دستور پینگ
# ==========================================================
@client.on(events.NewMessage(pattern=r"^(?:\.ping|پینگ)$"))
async def ping(event):
    await event.reply("🏓 من فعالم و آماده‌ام!")

# ==========================================================
# 🔸 دستور پاکسازی سریع (نابود)
# ==========================================================
@client.on(events.NewMessage(pattern=r"^(?:\.nuke|نابود)(?:\s+(\d+))?$"))
async def nuke(event):
    sender = await event.get_sender()
    if sender.id != OWNER_ID:
        return await event.reply("🚫 فقط ادمین می‌تواند از این دستور استفاده کند!")

    chat_id = event.chat_id
    limit = int(event.pattern_match.group(1) or 1000)

    msg = await event.reply(f"🧹 در حال نابودی {limit} پیام اخیر...")

    try:
        messages = await client.get_messages(chat_id, limit=limit)
        ids = [m.id for m in messages]
        total = len(ids)
        deleted = 0
        failed = 0

        for batch in chunked(ids, BATCH_SIZE):
            try:
                await client.delete_messages(chat_id, batch, revoke=True)
                deleted += len(batch)
            except errors.FloodWait as fw:
                await msg.edit(f"⚠️ محدودیت حذف — صبر {fw.seconds}s ...")
                await asyncio.sleep(fw.seconds + 1)
            except Exception as e:
                print(f"[NUKE ERROR] {e}")
                failed += len(batch)

            await msg.edit(f"🧹 حذف شد: {deleted}/{total} (ناموفق: {failed})")
            await asyncio.sleep(SLEEP_BETWEEN)

        await msg.edit(f"✅ پاکسازی انجام شد!\n🧾 حذف‌شده: {deleted}\n❌ ناموفق: {failed}")

    except Exception as e:
        await msg.edit(f"❌ خطا در پاکسازی: {e}")

# ==========================================================
# 🔸 دستور توقف پینگ (برای سایلنت موقت)
# ==========================================================
ping_block = set()

@client.on(events.NewMessage(pattern=r"^(?:توقف پینگ)$"))
async def stop_ping(event):
    sender = await event.get_sender()
    if sender.id != OWNER_ID:
        return await event.reply("🚫 فقط ادمین می‌تواند پینگ را متوقف کند!")

    ping_block.add(event.chat_id)
    await event.reply("🔕 پاسخ پینگ در این چت غیرفعال شد.")

@client.on(events.NewMessage(pattern=r"^(?:فعال‌سازی پینگ)$"))
async def enable_ping(event):
    sender = await event.get_sender()
    if sender.id != OWNER_ID:
        return await event.reply("🚫 فقط ادمین می‌تواند پینگ را فعال کند!")

    if event.chat_id in ping_block:
        ping_block.remove(event.chat_id)
        await event.reply("🔔 پاسخ پینگ دوباره فعال شد.")
    else:
        await event.reply("ℹ️ پینگ از قبل فعال بوده.")

# ==========================================================
# 🔸 دستورات بن / سکوت / اخطار (نمایشی ساده)
# ==========================================================
@client.on(events.NewMessage(pattern=r"^(?:بن|سکوت|اخطار)(?:\s+@?\w+)?$"))
async def moderation(event):
    text = event.raw_text.strip()
    target = event.pattern_match.group(0).split(" ", 1)
    action = text.split()[0]
    user = target[1] if len(target) > 1 else "کاربر نامشخص"
    await event.reply(f"⚙️ دستور {action} برای {user} ثبت شد (در حالت نمایشی).")

# ==========================================================
# 🚀 شروع یوزربات
# ==========================================================
print("✅ یوزربات در حال اتصال ...")
client.start()
me = client.loop.run_until_complete(client.get_me())
print(f"🤖 یوزربات فعال شد ({me.first_name}) [ID: {me.id}]")

client.run_until_disconnected()
