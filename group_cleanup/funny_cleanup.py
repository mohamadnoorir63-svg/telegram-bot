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
FAST_DELETE_THRESHOLD = 200
SLEEP_SEC = 0.15
SUDO_IDS = [8588347189]

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

# ================== ⚡ حذف پیام‌ها ==================
async def _batch_delete(context, chat_id: int, ids: list[int], fast: bool = False) -> int:
    if not ids:
        return 0
    results = await asyncio.gather(
        *[context.bot.delete_message(chat_id, mid) for mid in ids],
        return_exceptions=True
    )
    if not fast:
        await asyncio.sleep(SLEEP_SEC)
    return sum(1 for r in results if not isinstance(r, Exception))

async def _delete_messages(context, chat_id: int, mids: list[int]) -> int:
    if len(mids) <= FAST_DELETE_THRESHOLD:
        return await _batch_delete(context, chat_id, mids, fast=True)
    deleted = 0
    for i in range(0, len(mids), BATCH_SIZE):
        batch = mids[i:i + BATCH_SIZE]
        deleted += await _batch_delete(context, chat_id, batch)
    return deleted

async def _delete_all_messages(context, chat_id: int, last_msg_id: int) -> int:
    mids = list(range(last_msg_id, 0, -1))
    return await _delete_messages(context, chat_id, mids)

async def _delete_last_n(context, chat_id: int, last_msg_id: int, n: int) -> int:
    start = max(1, last_msg_id - n)
    mids = list(range(last_msg_id, start - 1, -1))
    return await _delete_messages(context, chat_id, mids)

async def _delete_by_user_from_buffer(context, chat_id: int, user_id: int) -> int:
    mids = [mid for mid, uid in reversed(track_map.get(chat_id, [])) if uid == user_id]
    return await _delete_messages(context, chat_id, mids)

# ================== یوزربات ==================
try:
    from userbot_module.userbot import client as userbot_client
except ImportError:
    userbot_client = None

async def delete_via_userbot(chat_id: int, message_ids: list[int]):
    """پاکسازی سریع با یوزربات"""
    if not userbot_client or not message_ids:
        return 0
    deleted = 0
    chunk_size = 20
    for i in range(0, len(message_ids), chunk_size):
        batch = message_ids[i:i + chunk_size]
        for mid in batch:
            try:
                await userbot_client.delete_messages(chat_id, mid)
                deleted += 1
            except:
                continue
        await asyncio.sleep(0.05)
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

    # 🧼 پاکسازی کامل
    if text in ("پاکسازی", "clean"):
        message_ids = list(range(msg.message_id, 0, -1))
        action_type = "🧼 پاکسازی کامل از اولین تا آخرین پیام"

    # 🧑‍💻 حذف پیام‌های فرد خاص
    elif msg.reply_to_message and (text.startswith("پاک") or text.startswith("حذف")):
        target = msg.reply_to_message.from_user
        message_ids = [mid for mid, uid in reversed(track_map.get(chat.id, [])) if uid == target.id]
        action_type = f"🧑‍💻 حذف پیام‌های {target.first_name}"

    # 🔢 حذف عددی
    elif text.startswith("حذف") or text.startswith("پاک"):
        try:
            n = int(args[0]) if args else int(text.split()[1])
        except:
            return await msg.reply_text("⚙️ فرمت درست: حذف 100")
        n = max(1, min(n, MAX_BULK))
        message_ids = list(range(msg.message_id, msg.message_id - n, -1))
        action_type = f"🧹 حذف عددی {n} پیام"

    else:
        return

    # حذف خود دستور
    try:
        await msg.delete()
    except:
        pass

    # اجرای پاکسازی
    if userbot_client:
        deleted = await delete_via_userbot(chat.id, message_ids)
    else:
        deleted = await _delete_messages(context, chat.id, message_ids)

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
    application.add_handler(CommandHandler("clean", funny_cleanup))
    application.add_handler(
        MessageHandler(
            (filters.TEXT & ~filters.COMMAND) &
            filters.Regex(r"^(?:پاکسازی|پاک(?:\s+\d+)?|حذف(?:\s+\d+)?)$"),
            funny_cleanup
        )
    )
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, track_message))
