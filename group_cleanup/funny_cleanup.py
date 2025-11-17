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
USERBOT_ID = 8203554172  # ⬅ آیدی یوزربات را اینجا بگذار

HEAVY_LIMIT = 600  # بالاتر از این مقدار → پاکسازی توسط یوزربات

# ================== 🧠 بافر پیام‌ها ==================

track_map: dict[int, Deque[Tuple[int, int]]] = defaultdict(lambda: deque(maxlen=TRACK_BUFFER))

async def track_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if msg and update.effective_chat.type in ("group", "supergroup"):
        track_map[update.effective_chat.id].append((msg.message_id, getattr(msg.from_user, "id", None)))

# ================== 🔐 دسترسی ==================

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
        deleted += await _batch_delete(context, chat_id, mids[i:i + BATCH_SIZE])
    return deleted

async def _delete_last_n(context, chat_id: int, last_msg_id: int, n: int) -> int:
    start = max(1, last_msg_id - n)
    mids = list(range(last_msg_id, start - 1, -1))
    return await _delete_messages(context, chat_id, mids)

async def _delete_by_user_from_buffer(context, chat_id: int, user_id: int) -> int:
    mids = [mid for mid, uid in reversed(track_map.get(chat_id, [])) if uid == user_id]
    return await _delete_messages(context, chat_id, mids)

async def _delete_all(context, chat_id: int) -> int:
    """پاکسازی همه پیام‌ها از اولین تا آخرین بدون استثنا"""
    tracked = track_map.get(chat_id, [])
    if not tracked:
        return 0
    mids = sorted([mid for mid, _ in tracked])
    return await _delete_messages(context, chat_id, mids)

# ================== 🤝 هماهنگی با یوزربات ==================

async def send_cleanup_to_userbot(context, chat_id: int, last_id: int, count: int | None):
    """ارسال فرمان پاکسازی سنگین به یوزربات"""
    cmd = f"cleanup|{chat_id}|{last_id}|{count or ''}".rstrip("|")
    try:
        await context.bot.send_message(USERBOT_ID, cmd)
        return True
    except:
        return False

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
        total_msgs = len(track_map.get(chat.id, []))
        if total_msgs > HEAVY_LIMIT:
            ok = await send_cleanup_to_userbot(context, chat.id, None, None)
            if ok:
                return await msg.reply_text("🧹 پاکسازی سنگین توسط یوزربات انجام می‌شود…")
        deleted = await _delete_all(context, chat.id)
        action_type = "🧼 پاکسازی کامل (همه پیام‌ها بدون استثنا)"

    # 🧍 حذف پیام‌های یک کاربر
    elif msg.reply_to_message:
        target = msg.reply_to_message.from_user
        deleted = await _delete_by_user_from_buffer(context, chat.id, target.id)
        action_type = f"🧑‍💻 حذف پیام‌های {target.first_name}"

    # 🔢 حذف عددی
    elif text.startswith("حذف") or text.startswith("پاک"):
        try:
            n = int(args[0]) if args else int(text.split()[1])
        except:
            return await msg.reply_text("⚙️ فرمت درست: حذف 50")

        n = max(1, min(n, MAX_BULK))
        if n > HEAVY_LIMIT:
            ok = await send_cleanup_to_userbot(context, chat.id, msg.message_id, n)
            if ok:
                return await msg.reply_text(f"🧹 حذف {n} پیام توسط یوزربات انجام می‌شود…")
        deleted = await _delete_last_n(context, chat.id, msg.message_id, n)
        action_type = f"🧹 حذف {n} پیام"

    else:
        return

    # حذف پیام دستور
    try:
        await msg.delete()
    except:
        pass

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

# ================== 🔧 ثبت هندلر ==================

def register_cleanup_handlers(application):
    application.add_handler(CommandHandler("clean", funny_cleanup))
    application.add_handler(
        MessageHandler(
            (filters.TEXT & ~filters.COMMAND) &
            filters.Regex(r"^(?:پاکسازی|پاک(?:\s+\d+)?|حذف(?:\s+\d+)?)$"),
            funny_cleanup
        )
    )
    application.add_handler(
        MessageHandler(filters.ALL & ~filters.COMMAND, track_message)
    )
