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

USERBOT_ID = 777777777      # آیدی یوزربات
HEAVY_LIMIT = 600           # پاکسازی سنگین → یوزربات

# ================== 🧠 بافر پیام‌ها ==================

# ذخیره تمام پیام‌ها شامل ربات‌ها و مدیران
track_map: dict[int, Deque[Tuple[int, int]]] = defaultdict(lambda: deque(maxlen=TRACK_BUFFER))

async def track_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if msg and update.effective_chat.type in ("group", "supergroup"):
        # ذخیره همه پیام‌ها حتی ربات‌ها و مدیران
        track_map[update.effective_chat.id].append((msg.message_id, msg.from_user.id if msg.from_user else None))

# ================== 🔐 دسترسی ==================

async def _has_access(context, chat_id, user_id):
    if user_id in SUDO_IDS:
        return True
    try:
        m = await context.bot.get_chat_member(chat_id, user_id)
        return m.status in ("creator", "administrator")
    except:
        return False

# ================== ⚡ حذف پیام‌ها ==================

async def _batch_delete(context, chat_id, ids, fast=False):
    if not ids:
        return 0
    res = await asyncio.gather(
        *[context.bot.delete_message(chat_id, mid) for mid in ids],
        return_exceptions=True
    )
    if not fast:
        await asyncio.sleep(SLEEP_SEC)
    return sum(1 for r in res if not isinstance(r, Exception))

async def _delete_messages(context, chat_id, mids):
    if len(mids) <= FAST_DELETE_THRESHOLD:
        return await _batch_delete(context, chat_id, mids, fast=True)
    deleted = 0
    for i in range(0, len(mids), BATCH_SIZE):
        deleted += await _batch_delete(context, chat_id, mids[i:i+BATCH_SIZE])
    return deleted

async def _delete_all_messages(context, chat_id, last_id):
    mids = list(range(last_id, 0, -1))
    return await _delete_messages(context, chat_id, mids)

async def _delete_last_n(context, chat_id, last_id, n):
    start = max(1, last_id - n)
    mids = list(range(last_id, start-1, -1))
    return await _delete_messages(context, chat_id, mids)

async def _delete_by_user(context, chat_id, user_id):
    mids = [mid for mid, uid in reversed(track_map[chat_id]) if uid == user_id or uid is None]
    return await _delete_messages(context, chat_id, mids)

# ================== 🤝 هماهنگی با یوزربات ==================

async def send_cleanup_to_userbot(context, chat_id, last_id, count_or_list):
    if isinstance(count_or_list, list):
        mids = ",".join(str(i) for i in count_or_list)
        cmd = f"cleanup|{chat_id}|{last_id}|{mids}"
    elif count_or_list:
        cmd = f"cleanup|{chat_id}|{last_id}|{count_or_list}"
    else:
        cmd = f"cleanup|{chat_id}|{last_id}"

    try:
        await context.bot.send_message(USERBOT_ID, cmd)
        return True
    except:
        return False

# ================== 🧹 فرمان اصلی ==================

async def funny_cleanup(update, context):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user
    text = (msg.text or "").strip().lower()
    args = context.args

    if chat.type not in ("group", "supergroup"):
        return await msg.reply_text("❌ فقط داخل گروه")

    if not await _has_access(context, chat.id, user.id):
        return await msg.reply_text("🚫 فقط مدیران")

    deleted = 0

    # --- پاکسازی کامل ---
    if text in ("پاکسازی", "clean"):
        if msg.message_id > HEAVY_LIMIT:
            if await send_cleanup_to_userbot(context, chat.id, msg.message_id, None):
                return await msg.reply_text("🧹 پاکسازی سنگین توسط یوزربات انجام می‌شود…")
        deleted = await _delete_all_messages(context, chat.id, msg.message_id)

    # --- حذف پیام‌های یک کاربر ---
    elif msg.reply_to_message and (text.startswith("پاک") or text.startswith("حذف")):
        target = msg.reply_to_message.from_user
        mids = [mid for mid, uid in reversed(track_map[chat.id]) if uid == target.id or uid is None]
        if len(mids) > HEAVY_LIMIT:
            if await send_cleanup_to_userbot(context, chat.id, msg.message_id, mids):
                return await msg.reply_text("🧑‍💻 حذف پیام‌های کاربر توسط یوزربات انجام شد")
        deleted = await _delete_by_user(context, chat.id, target.id)

    # --- حذف عددی ---
    elif text.startswith("حذف") or text.startswith("پاک"):
        try:
            n = int(args[0]) if args else int(text.split()[1])
        except:
            return await msg.reply_text("فرمت صحیح: حذف 100")
        n = max(1, min(n, MAX_BULK))
        if n > HEAVY_LIMIT:
            if await send_cleanup_to_userbot(context, chat.id, msg.message_id, n):
                return await msg.reply_text(f"🧹 حذف {n} پیام توسط یوزربات انجام می‌شود")
        deleted = await _delete_last_n(context, chat.id, msg.message_id, n)

    else:
        return

    try:
        await msg.delete()
    except:
        pass

    try:
        await context.bot.send_message(chat.id, f"✅ انجام شد\nتعداد: {deleted}")
    except:
        pass

# ================== رجیستر ==================

def register_cleanup_handlers(app):
    app.add_handler(CommandHandler("clean", funny_cleanup))
    app.add_handler(
        MessageHandler(
            (filters.TEXT & ~filters.COMMAND) &
            filters.Regex(r"^(?:پاکسازی|پاک(?:\s+\d+)?|حذف(?:\s+\d+)?)$"),
            funny_cleanup
        )
    )
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, track_message))
