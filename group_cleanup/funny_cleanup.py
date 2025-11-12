import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

# ================== ⚙️ تنظیمات ==================
MAX_BULK = 10000
BATCH_SIZE = 20
SLEEP_SEC = 0.2
SUDO_IDS = [8588347189]  # آیدی سودو

# ---------- یوزربات ----------
try:
    from userbot_module.userbot import client as userbot_client
except ImportError:
    userbot_client = None

# ================== 🔐 بررسی دسترسی ==================
async def _has_access(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> bool:
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except:
        return False

# ================== 🗑️ حذف پیام‌ها ==================
async def _batch_delete_telegram(context, chat_id: int, ids: list[int]) -> int:
    deleted = 0
    tasks = []
    for mid in ids:
        tasks.append(context.bot.delete_message(chat_id, mid))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for r in results:
        if not isinstance(r, Exception):
            deleted += 1
    return deleted

async def _batch_delete_userbot(chat_id: int, ids: list[int]) -> int:
    if not userbot_client or not ids:
        return 0
    deleted = 0
    for mid in ids:
        try:
            await userbot_client.delete_messages(chat_id, mid)
            deleted += 1
        except:
            continue
        await asyncio.sleep(0.05)
    return deleted

async def _delete_messages(context, chat_id: int, mids: list[int]) -> int:
    deleted = 0
    for i in range(0, len(mids), BATCH_SIZE):
        batch = mids[i:i + BATCH_SIZE]
        deleted += await _batch_delete_telegram(context, chat_id, batch)
        if deleted < len(batch):
            # fallback به یوزربات برای پیام‌های باقی‌مانده
            deleted += await _batch_delete_userbot(chat_id, batch)
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

    # ---------- پاکسازی کامل ----------
    if text in ("پاکسازی", "clean"):
        if userbot_client:
            # گرفتن همه پیام‌ها با یوزربات
            try:
                messages = [m.id for m in await userbot_client.get_messages(chat.id, limit=MAX_BULK)]
                deleted = await _delete_messages(context, chat.id, messages)
            except Exception as e:
                await msg.reply_text(f"⚠️ خطا در یوزربات: {e}")
        else:
            # fallback: فقط پیام‌های اخیر از آخرین پیام تا حد MAX_BULK
            last_id = msg.message_id
            messages = list(range(last_id, max(1, last_id - MAX_BULK), -1))
            deleted = await _delete_messages(context, chat.id, messages)
        action_type = "🧼 پاکسازی کامل با یوزربات و ربات اصلی"

    # ---------- حذف پیام‌های ریپلای شده ----------
    elif msg.reply_to_message and (text.startswith("پاک") or text.startswith("حذف")):
        target = msg.reply_to_message.from_user
        messages = []
        if userbot_client:
            try:
                # گرفتن همه پیام‌های کاربر با یوزربات
                msgs = await userbot_client.get_messages(chat.id, limit=MAX_BULK)
                messages = [m.id for m in msgs if m.sender_id == target.id]
            except:
                pass
        if not messages:
            # fallback: حذف از آخرین تا MAX_BULK پیام
            messages = list(range(msg.message_id, max(1, msg.message_id - MAX_BULK), -1))
        deleted = await _delete_messages(context, chat.id, messages)
        action_type = f"🧑‍💻 حذف پیام‌های {target.first_name}"

    # ---------- حذف عددی ----------
    elif text.startswith("حذف") or text.startswith("پاک"):
        try:
            n = int(args[0]) if args else int(text.split()[1])
        except:
            return await msg.reply_text("⚙️ فرمت درست: حذف 100")
        n = max(1, min(n, MAX_BULK))
        messages = []
        if userbot_client:
            try:
                msgs = await userbot_client.get_messages(chat.id, limit=n)
                messages = [m.id for m in msgs]
            except:
                messages = list(range(msg.message_id, max(1, msg.message_id - n), -1))
        else:
            messages = list(range(msg.message_id, max(1, msg.message_id - n), -1))
        deleted = await _delete_messages(context, chat.id, messages)
        action_type = f"🧹 حذف عددی {n} پیام"

    else:
        return

    # حذف پیام دستور
    try:
        await msg.delete()
    except:
        pass

    await asyncio.sleep(0.5)
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
            (filters.TEXT & ~filters.COMMAND)
            & filters.Regex(r"^(?:پاکسازی|پاک(?:\s+\d+)?|حذف(?:\s+\d+)?)$"),
            funny_cleanup
        )
    )
