import asyncio
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

# ======================= 🧹 پاکسازی خنده‌دار =======================
async def funny_cleanup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پاکسازی فانتزی پیام‌ها با افکت خنده‌دار 😄"""
    chat = update.effective_chat
    user = update.effective_user
    args = context.args

    if chat.type not in ["group", "supergroup"]:
        return await update.message.reply_text("😂 این دستور فقط تو گروه کار می‌کنه قربان!")

    # بررسی مدیر بودن
    member = await context.bot.get_chat_member(chat.id, user.id)
    if member.status not in ["creator", "administrator"]:
        return await update.message.reply_text("😜 فقط مدیرای باحال می‌تونن پاکسازی کنن!")

    # تعداد پیام‌ها
    try:
        count = int(args[0]) if args else 15
        if count > 150:
            count = 150
    except:
        count = 15

    # انیمیشن خنده‌دار قبل از حذف
    steps = [
        "🧹 در حال جارو کشیدن گروه...",
        "💨 گرد و خاک رفت هوا!",
        "🪣 آب و صابون آماده شد...",
        "🤖 خنگول دست به کار شد...",
        "😎 پیام‌ها دارن پاک می‌شن..."
    ]

    msg = await update.message.reply_text("🧼 شروع عملیات پاکسازی خنگولی 😅", parse_mode="HTML")
    for step in steps:
        await asyncio.sleep(0.8)
        try:
            await msg.edit_text(step)
        except:
            pass

    deleted = 0
    async for m in context.bot.get_chat_history(chat.id, limit=count + 1):
        try:
            await context.bot.delete_message(chat.id, m.message_id)
            deleted += 1
            await asyncio.sleep(0.05)
        except:
            pass

    # پیام نهایی
    final_text = (
        f"✅ <b>پاکسازی با موفقیت انجام شد!</b>\n"
        f"🧹 تعداد پیام‌های حذف‌شده: <b>{deleted}</b>\n"
        f"😂 گروه تمیز شد، خنگول برق انداخت!\n\n"
        f"🌙 توسط: <b>{user.first_name}</b>"
    )
    try:
        await msg.edit_text(final_text, parse_mode="HTML")
    except:
        await update.message.reply_text(final_text, parse_mode="HTML")

# ======================= ⚙️ رجیستر هندلرها =======================
def register_cleanup_handlers(application):
    """افزودن هندلرهای پاکسازی به برنامه اصلی"""
    application.add_handler(CommandHandler("clean", funny_cleanup))
    application.add_handler(CommandHandler("پاکسازی", funny_cleanup))
