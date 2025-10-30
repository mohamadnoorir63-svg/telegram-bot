# ==========================================================
# 🤖 Userbot پیشرفته با سیستم Checkpoint و کنترل توقف
# ==========================================================
import os
import json
import asyncio
from pathlib import Path
from telethon import TelegramClient, events, errors
from telethon.sessions import StringSession

# ─────────────── تنظیمات پایه ───────────────
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION = os.getenv("SESSION_STRING", "")
OWNER_IDS = {7089376754}  # ← آیدی خودت یا چند ادمین مجاز

if not API_ID or not API_HASH:
    raise SystemExit("⚠️ لطفاً API_ID و API_HASH را در env تنظیم کن.")

client = TelegramClient(StringSession(SESSION) if SESSION else "userbot.session", API_ID, API_HASH)

# ─────────────── تنظیمات پاکسازی ───────────────
BATCH_SIZE = 100
SLEEP_BETWEEN_BATCH = 0.4

# ==========================================================
# 📂 مدیریت فایل‌های checkpoint برای ادامه عملیات
# ==========================================================
CHECKPOINT_DIR = Path("userbot_checkpoints")
CHECKPOINT_DIR.mkdir(exist_ok=True)

active_jobs: dict[int, asyncio.Event] = {}  # chat_id -> cancel event

def _checkpoint_path(chat_id: int) -> Path:
    return CHECKPOINT_DIR / f"obliterate_{chat_id}.json"

def save_checkpoint(chat_id: int, remaining_ids: list[int]):
    try:
        with open(_checkpoint_path(chat_id), "w", encoding="utf-8") as f:
            json.dump({"remaining": remaining_ids}, f)
    except Exception as e:
        print("⚠️ خطا در ذخیره checkpoint:", e)

def load_checkpoint(chat_id: int) -> list[int] | None:
    p = _checkpoint_path(chat_id)
    if not p.exists():
        return None
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("remaining", []) or []
    except Exception as e:
        print("⚠️ خطا در بارگذاری checkpoint:", e)
        return None

def clear_checkpoint(chat_id: int):
    try:
        p = _checkpoint_path(chat_id)
        if p.exists():
            p.unlink()
    except:
        pass


# ==========================================================
# 🧠 دستور لغو عملیات پاکسازی (abort)
# ==========================================================
@client.on(events.NewMessage(pattern=r"^(?:\.abort|توقف)$", incoming=True))
async def abort_handler(event):
    sender = await event.get_sender()
    if sender.id not in OWNER_IDS:
        return await event.reply("🚫 فقط ادمین‌ها می‌توانند عملیات را لغو کنند.")
    chat_id = event.chat_id
    ev = active_jobs.get(chat_id)
    if ev:
        ev.set()  # سیگنال لغو
        await event.reply("🛑 درخواست لغو ارسال شد — در حال توقف تدریجی...")
    else:
        await event.reply("ℹ️ فعلاً هیچ عملیاتی در حال اجرا نیست.")


# ==========================================================
# 🧹 دستور نابود (پاکسازی گروه با checkpoint و ادامه)
# ==========================================================
@client.on(events.NewMessage(pattern=r"^(?:\.nuke|نابود)(?:\s+(\d+))?$", incoming=True))
async def nuke_handler(event):
    sender = await event.get_sender()
    if sender.id not in OWNER_IDS:
        return await event.reply("🚫 فقط ادمین‌ها مجاز به اجرای «نابود» هستند.")

    chat_id = event.chat_id
    m = event.pattern_match.group(1)
    limit = int(m) if m else 5000

    start_msg = await event.reply("🧹 در حال آماده‌سازی پاکسازی...")

    try:
        messages = await client.get_messages(chat_id, limit=limit)
    except Exception as e:
        return await start_msg.edit(f"⚠️ خطا در دریافت پیام‌ها: {e}")

    # بررسی checkpoint قبلی
    remaining = load_checkpoint(chat_id)
    if remaining:
        ids = remaining
        await start_msg.edit("♻️ ادامه از آخرین وضعیت ذخیره‌شده...")
    else:
        ids = [m.id for m in messages]

    total = len(ids)
    deleted = 0
    failed = 0

    cancel_event = asyncio.Event()
    active_jobs[chat_id] = cancel_event

    await start_msg.edit(f"🧹 شروع حذف — {total} پیام در صف. (دسته‌ای {BATCH_SIZE})")

    try:
        for i in range(0, total, BATCH_SIZE):
            if cancel_event.is_set():
                await start_msg.edit(f"🛑 عملیات لغو شد توسط ادمین. حذف‌شده: {deleted}/{total}")
                save_checkpoint(chat_id, ids[i:])
                return

            batch = ids[i:i + BATCH_SIZE]
            try:
                await client.delete_messages(chat_id, batch, revoke=True)
                deleted += len(batch)
            except errors.FloodWait as fw:
                save_checkpoint(chat_id, ids[i:])
                await start_msg.edit(f"⚠️ FloodWait: باید {fw.seconds} ثانیه صبر کنیم... (checkpoint ذخیره شد)")
                await asyncio.sleep(fw.seconds + 2)
                try:
                    await client.delete_messages(chat_id, batch, revoke=True)
                    deleted += len(batch)
                    clear_checkpoint(chat_id)
                except Exception as e:
                    print("[nuke] error after flood:", e)
                    failed += len(batch)
            except Exception as e:
                print("[nuke] batch delete error:", e)
                failed += len(batch)

            try:
                await start_msg.edit(f"🧹 حذف شد: {deleted}/{total}  (ناموفق: {failed})")
            except:
                pass

            # ذخیره checkpoint دوره‌ای (هر 5 دسته)
            if (i // BATCH_SIZE) % 5 == 0:
                save_checkpoint(chat_id, ids[i + BATCH_SIZE:])

            await asyncio.sleep(SLEEP_BETWEEN_BATCH)

        clear_checkpoint(chat_id)
        await start_msg.edit(f"✅ پاکسازی پایان یافت.\n✔️ حذف‌شده: {deleted}\n❗ ناموفق: {failed}")
        await client.send_message(chat_id, f"✨ عملیات نابود با موفقیت پایان یافت.\n📉 {deleted} پیام حذف شد.")
    finally:
        active_jobs.pop(chat_id, None)


# ==========================================================
# 💬 پینگ تست
# ==========================================================
@client.on(events.NewMessage(pattern=r"^(?:\.ping|پینگ)$"))
async def ping_handler(event):
    await event.reply("🏓 یوزربات آماده به خدمت است ✅")


# ==========================================================
# 🚀 اجرای اصلی
# ==========================================================
if __name__ == "__main__":
    print("🔌 Userbot در حال اجراست...")
    client.start()
    client.run_until_disconnected()
