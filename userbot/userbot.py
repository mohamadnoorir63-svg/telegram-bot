# ==========================================================
# 🤖 Userbot فارسی چندمنظوره (پاکسازی، بن، سکوت، اخطار)
# ==========================================================
import os
import asyncio
from telethon import TelegramClient, events, errors
from telethon.sessions import StringSession

# ---- تنظیمات محیطی ----
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION = os.getenv("SESSION_STRING", "")
OWNER_IDS = {7089376754}  # آیدی مدیران مجاز (خودت + دیگران در صورت نیاز)

if not API_ID or not API_HASH:
    raise SystemExit("⚠️ لطفاً API_ID و API_HASH را در محیط تنظیم کن.")

client = TelegramClient(StringSession(SESSION) if SESSION else "userbot.session", API_ID, API_HASH)

# ---- تنظیمات پاکسازی ----
NUKE_BATCH = 100
NUKE_SLEEP = 0.3
NUKE_DEFAULT = 5000
STOP_NUKE = False


# ==========================================================
# 🩵 دستور پینگ / Ping
# ==========================================================
@client.on(events.NewMessage(pattern=r"^(?:\.ping|پینگ)$"))
async def ping_handler(event):
    await event.reply("🏓 یوزربات فعاله ✅")


# ==========================================================
# 🔥 پاکسازی سریع / نابود
# ==========================================================
@client.on(events.NewMessage(pattern=r"^(?:\.nuke|نابود)(?:\s+(\d+))?$"))
async def nuke_handler(event):
    global STOP_NUKE
    sender = await event.get_sender()
    if sender.id not in OWNER_IDS:
        await event.reply("🚫 شما اجازه اجرای این دستور را ندارید.")
        return

    m = event.pattern_match.group(1)
    limit = int(m) if m else NUKE_DEFAULT
    chat_id = event.chat_id
    msg = await event.reply(f"🧹 در حال جمع‌آوری آخرین {limit} پیام...")

    try:
        messages = await client.get_messages(chat_id, limit=limit)
        ids = [m.id for m in messages]
        total = len(ids)
        deleted = 0
        failed = 0
        STOP_NUKE = False

        for i in range(0, total, NUKE_BATCH):
            if STOP_NUKE:
                await msg.edit(f"⛔ عملیات نابود متوقف شد!\n✅ حذف‌شده: {deleted}\n❌ ناموفق: {failed}")
                return

            batch = ids[i:i + NUKE_BATCH]
            try:
                await client.delete_messages(chat_id, batch, revoke=True)
                deleted += len(batch)
            except errors.FloodWait as fw:
                await msg.edit(f"⚠️ محدودیت حذف، انتظار {fw.seconds}s ...")
                await asyncio.sleep(fw.seconds)
            except Exception as e:
                print(f"[NUKE ERROR] {e}")
                failed += len(batch)

            await msg.edit(f"🧹 حذف شد: {deleted}/{total} (ناموفق: {failed})")
            await asyncio.sleep(NUKE_SLEEP)

        await msg.edit(f"✅ عملیات نابود پایان یافت!\n🧨 حذف‌شده: {deleted}\n🚫 ناموفق: {failed}")

        # اطلاع نهایی در گروه
        await client.send_message(chat_id, f"✨ پاکسازی کامل شد!\n📉 {deleted} پیام حذف شد.\n⚙️ Userbot آماده‌ست.")

    except Exception as e:
        await msg.edit(f"❌ خطا در پاکسازی: {e}")


# ==========================================================
# 🛑 توقف عملیات نابود
# ==========================================================
@client.on(events.NewMessage(pattern=r"^(?:\.stop|توقف)$"))
async def stop_handler(event):
    global STOP_NUKE
    STOP_NUKE = True
    await event.reply("🛑 عملیات نابود در حال توقف است...")


# ==========================================================
# 🚫 بن کاربر
# ==========================================================
@client.on(events.NewMessage(pattern=r"^(?:\.ban|بن)$"))
async def ban_user(event):
    if not event.is_reply:
        await event.reply("📎 باید روی پیام فرد ریپلای کنی تا بن شود.")
        return

    sender = await event.get_sender()
    if sender.id not in OWNER_IDS:
        await event.reply("🚫 شما مجوز بن ندارید.")
        return

    reply_msg = await event.get_reply_message()
    user = await reply_msg.get_sender()
    chat_id = event.chat_id

    try:
        await client.edit_permissions(chat_id, user.id, view_messages=False)
        await event.reply(f"⛔ کاربر [{user.first_name}](tg://user?id={user.id}) بن شد.")
    except Exception as e:
        await event.reply(f"❌ خطا در بن: {e}")


# ==========================================================
# 🔇 سکوت کاربر
# ==========================================================
@client.on(events.NewMessage(pattern=r"^(?:\.mute|سکوت)(?:\s+(\d+)\s*(ثانیه|دقیقه)?)?$"))
async def mute_user(event):
    if not event.is_reply:
        await event.reply("📎 باید روی پیام فرد ریپلای کنی تا ساکت شود.")
        return

    reply_msg = await event.get_reply_message()
    user = await reply_msg.get_sender()
    chat_id = event.chat_id
    m = event.pattern_match.group(1)
    unit = event.pattern_match.group(2)
    duration = None

    if m:
        seconds = int(m)
        if unit == "دقیقه":
            seconds *= 60
        duration = seconds

    try:
        until = None
        if duration:
            until = asyncio.get_event_loop().time() + duration
        await client.edit_permissions(chat_id, user.id, send_messages=False, until_date=until)
        await event.reply(f"🔇 کاربر [{user.first_name}](tg://user?id={user.id}) ساکت شد.")
    except Exception as e:
        await event.reply(f"❌ خطا در سکوت: {e}")


# ==========================================================
# 🔊 حذف سکوت
# ==========================================================
@client.on(events.NewMessage(pattern=r"^(?:\.unmute|حذف سکوت)$"))
async def unmute_user(event):
    if not event.is_reply:
        await event.reply("📎 باید روی پیام فرد ریپلای کنی تا سکوتش برداشته شود.")
        return

    reply_msg = await event.get_reply_message()
    user = await reply_msg.get_sender()
    chat_id = event.chat_id
    try:
        await client.edit_permissions(chat_id, user.id, send_messages=True)
        await event.reply(f"🔊 سکوت [{user.first_name}](tg://user?id={user.id}) برداشته شد.")
    except Exception as e:
        await event.reply(f"❌ خطا در حذف سکوت: {e}")


# ==========================================================
# ⚠️ اخطار
# ==========================================================
@client.on(events.NewMessage(pattern=r"^(?:\.warn|اخطار)$"))
async def warn_user(event):
    if not event.is_reply:
        await event.reply("📎 باید روی پیام فرد ریپلای کنی تا اخطار بگیرد.")
        return

    reply_msg = await event.get_reply_message()
    user = await reply_msg.get_sender()
    await event.reply(f"⚠️ کاربر [{user.first_name}](tg://user?id={user.id}) اخطار دریافت کرد.")


# ==========================================================
# 🚀 اجرا
# ==========================================================
if __name__ == "__main__":
    print("🔌 شروع userbot ...")
    client.start()
    client.run_until_disconnected()
