# userbot.py — Telethon userbot safe obliterate (Persian + ADMIN_IDS from env)
import os
import asyncio
from telethon import TelegramClient, events, errors
from telethon.sessions import StringSession

# ---------- تنظیمات اتصال ----------
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION = os.getenv("SESSION_STRING", "")  # یا فایل userbot.session

if not API_ID or not API_HASH:
    raise SystemExit("API_ID یا API_HASH تنظیم نشده‌اند. لطفاً متغیرهای محیطی را تنظیم کن.")

client = TelegramClient(StringSession(SESSION) if SESSION else "userbot.session", API_ID, API_HASH)

# ---------- تنظیمات ایمنی / قابل تنظیم ----------
# حالت خواندن ادمین‌ها از متغیر محیطی ADMIN_IDS (مثال: ADMIN_IDS=7089376754,123456789)
_admin_env = os.getenv("ADMIN_IDS", "").strip()
if _admin_env:
    try:
        OWNER_IDS = {int(x.strip()) for x in _admin_env.split(",") if x.strip()}
    except:
        OWNER_IDS = set()
else:
    OWNER_IDS = set()  # اگر خالی بمونه، هیچ‌کس اجازهٔ obliterate نداره — امن‌ترین حالت

# پیش‌فرض‌ها
DEFAULT_LIMIT = int(os.getenv("NUKE_DEFAULT_LIMIT", "5000"))
BATCH_SIZE = int(os.getenv("NUKE_BATCH_SIZE", "100"))
SLEEP_BETWEEN_BATCH = float(os.getenv("NUKE_SLEEP_BETWEEN_BATCH", "0.35"))

# ---------- کمکی: تقسیم لیست به دسته‌ها ----------
def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

# ---------- الگوها / واژه‌های پشتیبانی‌شده ----------
PREVIEW_WORDS = {"preview", "پیش", "پیشنمایش"}
CONFIRM_WORDS = {"confirm", "تایید", "تأیید", "قبول"}

# ---------- فرمان ایمن (فارسی و انگلیسی) ----------
# نمونه‌ها:
#   .نابود پیش 1000     -> پیش‌نمایش (فقط شمارش)
#   .نابود تایید 1000   -> اجرا (نیاز به بودن sender در ADMIN_IDS)
# پشتیبانی از: .نابود  .پاکسازی  .obliterate
@client.on(events.NewMessage(pattern=r"^(?:\.(?:obliterate|نابود|پاکسازی))(?:\s+([^\s]+))?(?:\s+(\d+))?$", incoming=True))
async def obliterate_handler(event):
    sender = await event.get_sender()
    sender_id = sender.id if sender else None
    arg1 = (event.pattern_match.group(1) or "").strip()
    arg2 = event.pattern_match.group(2)

    mode_word = arg1.lower()
    try:
        limit = int(arg2) if arg2 else DEFAULT_LIMIT
    except:
        limit = DEFAULT_LIMIT

    chat = await event.get_chat()
    chat_id = event.chat_id

    # فقط برای اطمینان: اگر OWNER_IDS خالی است، اجازه اجرا را نده
    if not OWNER_IDS:
        await event.reply("⚠️ فرمان غیرفعال است — هیچ ADMIN_IDS ای در متغیر محیطی تنظیم نشده.")
        return

    # حالت پیش‌نمایش (فقط شمارش پیام‌ها)
    if mode_word in PREVIEW_WORDS:
        info = await event.reply(f"🔎 در حال پیش‌نمایش: جمع‌آوری تا {limit} پیام ...")
        try:
            messages = await client.get_messages(chat_id, limit=limit)
            await info.edit(f"ℹ️ پیش‌نمایش: {len(messages)} پیام یافت شد (تا سقف {limit}).\n"
                            "اگر مطمئنی، از دستور با کلمهٔ تأیید استفاده کن:\n"
                            ".نابود تایید <تعداد>\nیا\n.نابود تایید (بدون عدد برای مقدار پیش‌فرض)")
        except Exception as e:
            await info.edit(f"⚠️ خطا در پیش‌نمایش: {e}")
        return

    # اگر کلمهٔ تأیید نیومده، هشدار بده (امن)
    if mode_word not in CONFIRM_WORDS:
        await event.reply(
            "⚠️ برای اجرای واقعی باید از یکی از این‌ها استفاده کنی:\n"
            "• .نابود پیش <عدد>  — پیش‌نمایش\n"
            "• .نابود تایید <عدد> — حذف واقعی (نیاز به مجوز)\n\n"
            "مثال: .نابود تایید 2000"
        )
        return

    # اجازهٔ اجرا تنها برای ادمین‌های مشخص‌شده
    if sender_id not in OWNER_IDS:
        await event.reply("🚫 شما مجوز اجرای این فرمان خطرناک را ندارید.")
        return

    # اعلام شروع
    start_msg = await event.reply("🔥 در حال آماده‌سازی برای پاکسازی — لطفاً صبر کن...")

    # دریافت پیام‌ها
    try:
        messages = await client.get_messages(chat_id, limit=limit)
    except Exception as e:
        await start_msg.edit(f"⚠️ خطا در دریافت پیام‌ها: {e}")
        return

    if not messages:
        await start_msg.edit("ℹ️ هیچ پیامی برای حذف یافت نشد.")
        return

    ids = [m.id for m in messages]
    total = len(ids)
    deleted = 0
    failed = 0

    await start_msg.edit(f"🧹 عملیات شروع شد — {total} پیام جمع‌آوری شد. حذف در دسته‌های {BATCH_SIZE} تایی.")

    for batch in chunks(ids, BATCH_SIZE):
        try:
            await client.delete_messages(chat_id, batch, revoke=True)
            deleted += len(batch)
        except errors.FloodWait as fw:
            await start_msg.edit(f"⚠️ FloodWait دریافت شد — باید {fw.seconds} ثانیه صبر کنیم...")
            await asyncio.sleep(fw.seconds + 1)
            try:
                await client.delete_messages(chat_id, batch, revoke=True)
                deleted += len(batch)
            except Exception as e:
                print("[obliterate] خطا پس از FloodWait:", e)
                failed += len(batch)
        except Exception as e:
            print("[obliterate] خطا در حذف دسته:", e)
            failed += len(batch)

        try:
            await start_msg.edit(f"🧹 حذف شد: {deleted}/{total}  (ناموفق: {failed})")
        except:
            pass

        await asyncio.sleep(SLEEP_BETWEEN_BATCH)

    await start_msg.edit(f"✅ پاکسازی پایان یافت.\n✔️ حذف شده: {deleted}\n❗ ناموفق: {failed}")

# ---------- اجرا ----------
if __name__ == "__main__":
    print("🔌 شروع userbot ...")
    client.start()
    client.run_until_disconnected()
