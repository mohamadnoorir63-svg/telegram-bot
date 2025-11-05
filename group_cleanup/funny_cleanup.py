import asyncio
from collections import deque, defaultdict
from typing import Deque, Tuple

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

# =============== تنظیمات ===============
DEFAULT_BULK = 300          # تعداد پیش‌فرض پاکسازی کلی
MAX_BULK = 10000            # سقف حذف عددی
TRACK_BUFFER = 600          # چند پیام آخر هر گروه برای حذف هدف‌دار (ریپلای) ذخیره شود
SLEEP_EVERY = 100           # هر 100 حذف، کمی مکث کند تا Flood نشود
SLEEP_SEC = 0.3

# =============== بافر ردیابی پیام‌ها ===============
# ساختار: track_map[chat_id] = deque[(message_id, from_user_id), ...]
track_map: dict[int, Deque[Tuple[int, int]]] = defaultdict(lambda: deque(maxlen=TRACK_BUFFER))

async def track_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هر پیامِ دیده‌شده را برای حذف هدف‌دار (ریپلای) ثبت می‌کنیم."""
    msg = update.effective_message
    if not msg or not msg.from_user:
        return
    if update.effective_chat and update.effective_chat.type in ("group", "supergroup"):
        track_map[update.effective_chat.id].append((msg.message_id, msg.from_user.id))

# =============== چک ادمین ===============
async def _is_admin(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> bool:
    try:
        m = await context.bot.get_chat_member(chat_id, user_id)
        return m.status in ("creator", "administrator")
    except:
        return False

# =============== هسته حذف ===============
async def _delete_last_n(context: ContextTypes.DEFAULT_TYPE, chat_id: int, last_msg_id: int, n: int) -> int:
    """حذف n پیام اخیر با تلاش روی IDهای نزولی (ساده‌ترین روش بدون history)."""
    deleted = 0
    start = max(1, last_msg_id - n)  # حداقل 1
    for mid in range(last_msg_id, start - 1, -1):
        try:
            await context.bot.delete_message(chat_id, mid)
            deleted += 1
        except:
            # ممکنه پیام متعلق به ربات نباشه/قدیمی باشه/اصلاً وجود نداشته باشه؛ رد می‌کنیم
            pass
        if deleted and deleted % SLEEP_EVERY == 0:
            await asyncio.sleep(SLEEP_SEC)
    return deleted

async def _delete_by_user_from_buffer(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> int:
    """حذف پیام‌های یک کاربر از پنجره‌ی اخیر (track_map)."""
    deleted = 0
    # روی کپی loop بزن تا حین حذف مشکل نداشته باشیم
    snapshot = list(track_map.get(chat_id, []))
    for mid, uid in reversed(snapshot):  # از جدید به قدیم
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

# =============== فرمان پاکسازی ===============
async def simple_cleanup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پاکسازی ساده:
    - «پاکسازی» یا «clean» → حذف پیش‌فرض (DEFAULT_BULK)
    - «حذف 123» یا «پاک 123» → حذف عددی
    - ریپلای + «پاک»/«حذف» → حذف پیام‌های اخیر همین کاربر از بافر
    """
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    if not chat or chat.type not in ("group", "supergroup"):
        return await msg.reply_text("این دستور فقط داخل گروه کار می‌کند.")

    if not await _is_admin(context, chat.id, user.id):
        return await msg.reply_text("فقط مدیران می‌توانند پاکسازی انجام دهند.")

    text = (msg.text or "").strip().lower()
    args = context.args

    deleted = 0

    # حالت ریپلای به یک کاربر: حذف پیام‌های او از بافر اخیر
    if msg.reply_to_message and (text.startswith("پاک") or text.startswith("حذف")):
        target = msg.reply_to_message.from_user
        deleted = await _delete_by_user_from_buffer(context, chat.id, target.id)
        return await msg.reply_text(f"حذف پیام‌های {target.first_name} انجام شد: {deleted} پیام.")

    # حالت «حذف n» یا «پاک n»
    if text.startswith("حذف") or text.startswith("پاک"):
        # تلاش برای خواندن عدد از آرگومان یا متن
        n = None
        if args and args[0].isdigit():
            n = int(args[0])
        else:
            parts = text.split()
            if len(parts) >= 2 and parts[1].isdigit():
                n = int(parts[1])
        if not n:
            n = DEFAULT_BULK
        n = max(1, min(n, MAX_BULK))
        deleted = await _delete_last_n(context, chat.id, msg.message_id, n)
        return await msg.reply_text(f"حذف انجام شد: {deleted} پیام.")

    # حالت «پاکسازی» یا «clean»: حذف پیش‌فرض
    if text in ("پاکسازی", "clean"):
        deleted = await _delete_last_n(context, chat.id, msg.message_id, DEFAULT_BULK)
        return await msg.reply_text(f"پاکسازی انجام شد: {deleted} پیام.")

    # اگر دستور تطبیق نشد، چیزی نگو
    return

# =============== رجیستر هندلرها ===============
def register_cleanup_handlers(application):
    # فرمان‌های /clean و معادل فارسی با اسلش انگلیسی فقط برای راحتی
    application.add_handler(CommandHandler("clean", simple_cleanup))
    # هندلر متنی برای فارسی/بدون اسلش
    application.add_handler(
        MessageHandler(
            (filters.TEXT & ~filters.COMMAND) &
            filters.Regex(r"^(?:پاکسازی|پاک(?:\s+\d+)?|حذف(?:\s+\d+)?)$")
            , simple_cleanup
        )
    )
    # ردیابی همه پیام‌های متنی/مدیا برای بافر (جهت حذف هدف‌دار)
    application.add_handler(
        MessageHandler(filters.ALL & ~filters.COMMAND, track_message)
    )
