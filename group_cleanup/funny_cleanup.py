import asyncio
from collections import deque, defaultdict
from datetime import datetime
from typing import Deque, Tuple
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

# ================== ⚙️ تنظیمات اصلی ==================
DEFAULT_BULK = 300          # تعداد پیش‌فرض پاکسازی کلی
MAX_BULK = 10000            # حداکثر تعداد مجاز پاک
TRACK_BUFFER = 600          # چند پیام آخر برای حذف هدف‌دار ذخیره می‌شود
SLEEP_EVERY = 100           # هر ۱۰۰ حذف یک توقف کوتاه
SLEEP_SEC = 0.3             # زمان توقف
SUDO_IDS = [8588347189]     # آیدی سودوها (اینجا آیدی خودت رو بگذار)

# ================== 🧠 ذخیره پیام‌ها برای حذف هدف‌دار ==================
track_map: dict[int, Deque[Tuple[int, int]]] = defaultdict(lambda: deque(maxlen=TRACK_BUFFER))

async def track_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هر پیام دریافتی را ذخیره می‌کند تا بعداً برای حذف هدف‌دار استفاده شود."""
    msg = update.effective_message
    if not msg or not msg.from_user:
        return
    if update.effective_chat and update.effective_chat.type in ("group", "supergroup"):
        track_map[update.effective_chat.id].append((msg.message_id, msg.from_user.id))

# ================== 🔐 بررسی سطح دسترسی ==================
async def _has_access(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> bool:
    """فقط مدیران و سودوها مجازند"""
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except:
        return False

# ================== 🗑️ توابع حذف ==================
async def _delete_last_n(context: ContextTypes.DEFAULT_TYPE, chat_id: int, last_msg_id: int, n: int) -> int:
    """حذف n پیام اخیر با حرکت به عقب در ID"""
    deleted = 0
    start = max(1, last_msg_id - n)
    for mid in range(last_msg_id, start - 1, -1):
        try:
            await context.bot.delete_message(chat_id, mid)
            deleted += 1
        except:
            pass
        if deleted and deleted % SLEEP_EVERY == 0:
            await asyncio.sleep(SLEEP_SEC)
    return deleted


async def _delete_by_user_from_buffer(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> int:
    """حذف پیام‌های اخیر یک کاربر (حتی اگر مدیر باشد)"""
    deleted = 0
    snapshot = list(track_map.get(chat_id, []))
    for mid, uid in reversed(snapshot):
        if uid != user_id:
            continue
        try:
            await context.bot.delete_message(chat_id, mid)
            deleted += 1
        except:
            pass
        if deleted and deleted % SLEEP_EVERY == 0:
            await asyncio.sleep(SLEEP_SEC)
    return deleted

# ================== 🧹 دستور اصلی پاکسازی ==================
async def funny_cleanup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    دستورات:
    🔹 «پاکسازی» → حذف کلی ۳۰۰ پیام آخر
    🔹 «حذف 200» یا «پاک 50» → حذف تعداد مشخص
    🔹 ریپلای + «پاک» یا «حذف» → حذف تمام پیام‌های اخیر کاربر مورد نظر
    """
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user
    text = (msg.text or "").strip().lower()
    args = context.args

    # فقط در گروه‌ها کار می‌کند
    if not chat or chat.type not in ("group", "supergroup"):
        return await msg.reply_text("🚫 این دستور فقط در گروه‌ها قابل استفاده است.")

    # فقط مدیران و سودوها مجازند
    if not await _has_access(context, chat.id, user.id):
        return await msg.reply_text("🚫 فقط مدیران یا سودوها اجازه استفاده از این دستور را دارند.")

    deleted = 0
    action_type = "نامشخص"

    # 🔸 حالت ریپلای → حذف پیام‌های فرد خاص
    if msg.reply_to_message and (text.startswith("پاک") or text.startswith("حذف")):
        target = msg.reply_to_message.from_user
        deleted = await _delete_by_user_from_buffer(context, chat.id, target.id)
        action_type = f"🧑‍💻 حذف پیام‌های {target.first_name}"

    # 🔸 حالت حذف عددی
    elif text.startswith("حذف") or text.startswith("پاک"):
        try:
            n = int(args[0]) if args else int(text.split()[1])
        except:
            n = DEFAULT_BULK
        n = max(1, min(n, MAX_BULK))
        deleted = await _delete_last_n(context, chat.id, msg.message_id, n)
        action_type = f"🧹 حذف عددی {n} پیام"

    # 🔸 حالت پاکسازی کلی
    elif text in ("پاکسازی", "clean"):
        deleted = await _delete_last_n(context, chat.id, msg.message_id, DEFAULT_BULK)
        action_type = "🧼 پاکسازی کلی"

    else:
        return

    # 🕓 گزارش نهایی
    time_now = datetime.now().strftime("%H:%M:%S")
    report = (
        f"✅ <b>گزارش پاکسازی</b>\n\n"
        f"{action_type}\n"
        f"📦 تعداد پیام‌های حذف‌شده: <b>{deleted}</b>\n"
        f"👤 دستوردهنده: <b>{user.first_name}</b>\n"
        f"🕓 ساعت اجرا: <code>{time_now}</code>"
    )

    await msg.reply_text(report, parse_mode="HTML")

# ================== 🔧 رجیستر هندلرها ==================
def register_cleanup_handlers(application):
    """ثبت هندلرها در برنامه اصلی"""
    application.add_handler(CommandHandler("clean", funny_cleanup))
    application.add_handler(
        MessageHandler(
            (filters.TEXT & ~filters.COMMAND)
            & filters.Regex(r"^(?:پاکسازی|پاک(?:\s+\d+)?|حذف(?:\s+\d+)?)$")
            , funny_cleanup
        )
    )
    application.add_handler(
        MessageHandler(filters.ALL & ~filters.COMMAND, track_message)
    )
