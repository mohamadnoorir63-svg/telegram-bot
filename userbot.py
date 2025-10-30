# userbot.py
# Telethon userbot for fast group purge (requires API_ID/API_HASH and session)
import os
import asyncio
from telethon import TelegramClient, events, errors
from telethon.sessions import StringSession

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION = os.getenv("SESSION_STRING", "")  # یا از فایل userbot.session استفاده کن

if not API_ID or not API_HASH:
    raise SystemExit("API_ID یا API_HASH تنظیم نشده‌اند. در متغیرهای محیطی قرار بده.")

# اگر SESSION داده شده باشه از StringSession استفاده می‌کنه، در غیر این‌صورت فایل session می‌سازه
if SESSION:
    client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
else:
    client = TelegramClient("userbot.session", API_ID, API_HASH)

# تنظیمات پاکسازی
BATCH_SIZE = 100          # تعداد پیام حذف در یک درخواست (حداکثر پیشنهادی)
SLEEP_BETWEEN_BATCH = 0.4 # وقفه بین دسته‌ها (برا جلوگیری از Flood) — می‌تونی کمتر کنی ولی ریسک رد از rate limit هست

# کمکی: تقسیم لیست به دسته‌ها
def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

@client.on(events.NewMessage(pattern=r"^\.ping$"))
async def ping_handler(event):
    await event.reply("🏓 Userbot فعاله ✅")

@client.on(events.NewMessage(pattern=r"^\.nuke(?:\s+(\d+))?$", incoming=True))
async def nuke_handler(event):
    """
    .nuke <limit?>
    اگر limit مشخص نشه، تا حد ممکن (حداکثر 20000 پیام اخیر) تلاش می‌کنه پاک کنه.
    توجه: حذف تمام تاریخچه ممکنه زمان و محدودیت داشته باشه.
    """
    sender = await event.get_sender()
    chat = await event.get_chat()
    chat_id = event.chat_id

    # دسترسی‌ها را چک کنیم
    try:
        # برای گروه/سوپرگروه باید یوزربوت ادمین باشه و حق حذف پیام داشته باشه
        if hasattr(chat, 'participant_count') or getattr(chat, 'megagroup', False) or getattr(chat, 'broadcast', False):
            # سعی می‌کنیم حقوق را چک کنیم (ممکن است خطا شود)
            me = await client.get_permissions(chat_id, "me")
        # get_permissions ممکن است در نسخه‌های قدیمی متفاوت باشد؛ صرفاً ادامه بدهیم و اجازه‌ را با عملیات حذف تست کنیم
    except Exception:
        pass

    # اعتبارسنجی تعداد
    m = event.pattern_match.group(1)
    limit = int(m) if m else None

    # اعلام شروع
    msg = await event.reply("🧹 شروع پاکسازی... در حال جمع‌آوری پیام‌ها ⌛")

    # جمع‌آوری پیام‌ها — محدودیت محافظتی
    # Telethon get_messages با limit کار می‌کند؛ اگر limit نباشد مقدار مناسبی انتخاب می‌کنیم
    fetch_limit = limit or 5000  # عدد پیش‌فرض؛ می‌تونی بالا ببری ولی خطر Rate/Memory هست
    if fetch_limit > 20000:
        fetch_limit = 20000

    try:
        # لیست پیام‌ها (پیام‌های اخیر)
        messages = await client.get_messages(chat_id, limit=fetch_limit)
        if not messages:
            await msg.edit("ℹ️ هیچ پیامی برای حذف یافت نشد.")
            return

        # ساخت لیست id ها (حذف در دسته‌ها)
        msg_ids = [m.id for m in messages]

        total = len(msg_ids)
        deleted = 0
        failed = 0

        # حذف در دسته‌ها
        for batch in chunks(msg_ids, BATCH_SIZE):
            try:
                # اگر گروه/چنل است می‌توان پیام‌های دیگران را حذف کرد در صورت داشتن permission
                await client.delete_messages(chat_id, batch, revoke=True)
                deleted += len(batch)
            except errors.FloodWait as fw:
                # سرویس به ما گفته صبر کنیم — پیام اطلاع بده و sleep کن
                await msg.edit(f"⚠️ FloodWait: صبر {fw.seconds} ثانیه لازم است...")
                await asyncio.sleep(fw.seconds + 1)
                try:
                    await client.delete_messages(chat_id, batch, revoke=True)
                    deleted += len(batch)
                except Exception:
                    failed += len(batch)
            except Exception as e:
                # خطای عمومی — ثبت و ادامه
                print(f"[NUKE ERROR] batch delete error: {e}")
                failed += len(batch)

            # بروزرسانی پیام وضعیت (هر چند دسته)
            try:
                await msg.edit(f"🧹 حذف شد: {deleted} / {total}    (ناموفق: {failed})")
            except: pass

            # جلوگیری از فشار بیش از حد — مقدار را کم/زیاد کن بر اساس تجربه و تست
            await asyncio.sleep(SLEEP_BETWEEN_BATCH)

        # پایان
        await msg.edit(f"✅ عملیات پاکسازی پایان یافت.\n✔️ حذف شده: {deleted}\n❗ ناموفق: {failed}")
    except Exception as e:
        await msg.edit(f"❌ خطا در پاکسازی: {e}")

# یک دستور امن‌تر: پاکسازی فقط پیام‌های بین پیام A و B یا ریپلای (پیشرفته‌تر قابل افزودن)
# می‌تونی handler های بیشتری اضافه کنی: .purge reply, .purge from @user, .purge last 100, و...

# اجرا
if __name__ == "__main__":
    print("🔌 شروع userbot ...")
    client.start()
    client.run_until_disconnected()
