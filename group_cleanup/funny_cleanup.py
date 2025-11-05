import asyncio
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, CommandHandler, filters

# ======================= 🧹 پاکسازی خنده‌دار =======================

async def funny_cleanup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پاکسازی پیشرفته با حالت‌های مختلف و افکت خنده‌دار 😄"""
    chat = update.effective_chat
    user = update.effective_user
    text = (update.message.text or "").strip().lower()
    args = context.args

    # فقط در گروه
    if chat.type not in ["group", "supergroup"]:
        return await update.message.reply_text("😂 این دستور فقط تو گروه کار می‌کنه قربان!")

    # فقط مدیر / سودو
    member = await context.bot.get_chat_member(chat.id, user.id)
    if member.status not in ["creator", "administrator"]:
        return await update.message.reply_text("😜 فقط مدیرای باحال می‌تونن پاکسازی کنن!")

    # شروع افکت خنده‌دار
    msg = await update.message.reply_text("🧼 خنگول داره آماده می‌شه برای پاکسازی...", parse_mode="HTML")
    steps = [
        "🧹 در حال جارو کشیدن گروه...",
        "💨 گرد و خاک رفت هوا!",
        "🪣 آب و صابون آماده شد...",
        "🤖 خنگول دست به کار شد...",
        "😎 پیام‌ها دارن پاک می‌شن..."
    ]
    for s in steps:
        await asyncio.sleep(0.6)
        try:
            await msg.edit_text(s)
        except:
            pass

    deleted = 0

    # ======================= حالت ۱: پاکسازی کلی =======================
    if text in ["پاکسازی", "clean", "پاک"]:
        async for m in context.bot.get_chat_history(chat.id, limit=5000):
            try:
                await context.bot.delete_message(chat.id, m.message_id)
                deleted += 1
                if deleted % 100 == 0:
                    await asyncio.sleep(0.5)
            except:
                pass

    # ======================= حالت ۲: حذف عددی =======================
    elif text.startswith("حذف") or text.startswith("پاک "):
        try:
            count = int(args[0]) if args else int(text.split()[1])
            if count > 10000:
                count = 10000
        except:
            count = 50
        async for m in context.bot.get_chat_history(chat.id, limit=count + 1):
            try:
                await context.bot.delete_message(chat.id, m.message_id)
                deleted += 1
                if deleted % 100 == 0:
                    await asyncio.sleep(0.5)
            except:
                pass

    # ======================= حالت ۳: ریپلای (پاک کردن پیام‌های یک نفر) =======================
    elif update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        target_id = target.id
        async for m in context.bot.get_chat_history(chat.id, limit=5000):
            if m.from_user and m.from_user.id == target_id:
                try:
                    await context.bot.delete_message(chat.id, m.message_id)
                    deleted += 1
                    if deleted % 100 == 0:
                        await asyncio.sleep(0.4)
                except:
                    pass

    # پیام پایانی
    try:
        await msg.edit_text(
            f"✅ <b>پاکسازی انجام شد!</b>\n"
            f"🧹 تعداد پیام‌های حذف‌شده: <b>{deleted}</b>\n"
            f"😂 گروه تمیز شد توسط <b>{user.first_name}</b>!",
            parse_mode="HTML"
        )
    except:
        await update.message.reply_text(
            f"✅ پاکسازی با موفقیت انجام شد!\nتعداد پیام‌های حذف‌شده: {deleted}",
            parse_mode="HTML"
        )


# ======================= ⚙️ رجیستر هندلرها =======================
def register_cleanup_handlers(application):
    """افزودن هندلرهای پاکسازی به برنامه اصلی"""

    # پشتیبانی از چند دستور
    commands = ["clean", "cleanup", "delete"]
    for cmd in commands:
        application.add_handler(CommandHandler(cmd, funny_cleanup))

    # پشتیبانی از دستورات فارسی (با یا بدون /)
    application.add_handler(
        MessageHandler(
            filters.Regex(r"^/?(پاکسازی|پاک|حذف)(\s+\d+)?$") & filters.TEXT,
            funny_cleanup
        )
    )
