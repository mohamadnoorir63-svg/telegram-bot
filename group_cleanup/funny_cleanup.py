import asyncio
from collections import deque, defaultdict
from datetime import datetime
from typing import Deque, Tuple
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

# ================== ⚙️ تنظیمات ==================
MAX_BULK = 10000
TRACK_BUFFER = 600
BATCH_SIZE = 20
SLEEP_SEC = 0.25
SUDO_IDS = [8588347189]  # آیدی سودو

# ================== 🧠 بافر پیام‌ها ==================
track_map: dict[int, Deque[Tuple[int, int]]] = defaultdict(lambda: deque(maxlen=TRACK_BUFFER))

async def track_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if msg and msg.from_user and update.effective_chat.type in ("group", "supergroup"):
        track_map[update.effective_chat.id].append((msg.message_id, msg.from_user.id))

# ================== 🔐 بررسی دسترسی ==================
async def _has_access(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> bool:
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except:
        return False

# ================== 🗑️ حذف سریع Batch ==================
async def _batch_delete(context, chat_id: int, ids: list[int]) -> int:
    """حذف گروهی پیام‌ها"""
    if not ids:
        return 0
    results = await asyncio.gather(
        *[context.bot.delete_message(chat_id, mid) for mid in ids],
        return_exceptions=True
    )
    return sum(1 for r in results if not isinstance(r, Exception))

async def _delete_all_messages(context, chat_id: int, last_msg_id: int) -> int:
    """پاکسازی کامل از اولین تا آخرین پیام گروه"""
    deleted = 0
    mid = last_msg_id
    while mid > 1:
        batch = list(range(mid, max(1, mid - BATCH_SIZE), -1))
        deleted += await _batch_delete(context, chat_id, batch)
        mid -= BATCH_SIZE
        await asyncio.sleep(SLEEP_SEC)
    return deleted

async def _delete_last_n(context, chat_id: int, last_msg_id: int, n: int) -> int:
    """حذف عددی n پیام آخر"""
    deleted = 0
    start = max(1, last_msg_id - n)
    mids = list(range(last_msg_id, start - 1, -1))
    for i in range(0, len(mids), BATCH_SIZE):
        batch = mids[i:i + BATCH_SIZE]
        deleted += await _batch_delete(context, chat_id, batch)
        await asyncio.sleep(SLEEP_SEC)
    return deleted

async def _delete_by_user_from_buffer(context, chat_id: int, user_id: int) -> int:
    """حذف تمام پیام‌های اخیر یک کاربر"""
    deleted = 0
    mids = [mid for mid, uid in reversed(track_map.get(chat_id, [])) if uid == user_id]
    for i in range(0, len(mids), BATCH_SIZE):
        batch = mids[i:i + BATCH_SIZE]
        deleted += await _batch_delete(context, chat_id, batch)
        await asyncio.sleep(SLEEP_SEC)
    return deleted

# ================== 🧹 دستور اصلی ==================
async def funny_cleanup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user
    text = (msg.text or "").strip().lower()
    args = context.args

    if chat.type not in ("group", "supergroup"):
        return await msg.reply_text("🚫 این دستور فقط در گروه‌ها قابل استفاده است.")

    if not await _has_access(context, chat.id, user.id):
        return await msg.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    deleted = 0
    action_type = "نامشخص"

    # 🧑‍💻 ریپلای → حذف پیام‌های فرد خاص
    if msg.reply_to_message and (text.startswith("پاک") or text.startswith("حذف")):
        target = msg.reply_to_message.from_user
        deleted = await _delete_by_user_from_buffer(context, chat.id, target.id)
        action_type = f"🧑‍💻 حذف پیام‌های {target.first_name}"

    # 🔢 حذف عددی
    elif text.startswith("حذف") or text.startswith("پاک"):
        try:
            n = int(args[0]) if args else int(text.split()[1])
        except:
            return await msg.reply_text("⚙️ فرمت درست: حذف 100")
        n = max(1, min(n, MAX_BULK))
        deleted = await _delete_last_n(context, chat.id, msg.message_id, n)
        action_type = f"🧹 حذف عددی {n} پیام"

    # 🧼 پاکسازی کامل
    elif text in ("پاکسازی", "clean"):
        deleted = await _delete_all_messages(context, chat.id, msg.message_id)
        action_type = "🧼 پاکسازی کامل از اولین تا آخرین پیام"

    else:
        return

    # حذف پیام دستور
    try:
        await msg.delete()
    except:
        pass

    # گزارش
    await asyncio.sleep(0.8)
    time_now = datetime.now().strftime("%H:%M:%S")
    report = (
        f"✅ <b>گزارش پاکسازی</b>\n\n"
        f"{action_type}\n"
        f"📦 پیام‌های حذف‌شده: <b>{deleted}</b>\n"
        f"👤 دستوردهنده: <b>{user.first_name}</b>\n"
        f"🕓 ساعت اجرا: <code>{time_now}</code>"
    )

    try:
        await context.bot.send_message(chat.id, report, parse_mode="HTML")
    except:
        pass

# ================== 🔧 رجیستر هندلرها ==================
def register_cleanup_handlers(application):
    """ثبت هندلرها در برنامه اصلی"""
    application.add_handler(CommandHandler("clean", funny_cleanup))
    application.add_handler(
        MessageHandler(
            (filters.TEXT & ~filters.COMMAND)
            & filters.Regex(r"^(?:پاکسازی|پاک(?:\s+\d+)?|حذف(?:\s+\d+)?)$"),
            funny_cleanup
        )
    )
    application.add_handler(
        MessageHandler(filters.ALL & ~filters.COMMAND, track_message)
    )
