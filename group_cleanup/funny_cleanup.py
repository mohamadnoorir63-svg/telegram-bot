import asyncio
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

# ======================= 🧹 پاکسازی خنده‌دار =======================
async def funny_cleanup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پاکسازی پیشرفته با سه حالت: کلی، عددی، و ریپلای 😄"""
    chat = update.effective_chat
    user = update.effective_user
    text = (update.message.text or "").strip().lower()
    args = context.args

    if chat.type not in ["group", "supergroup"]:
        return await update.message.reply_text("😂 این دستور فقط در گروه‌ها کار می‌کنه!")

    # بررسی مدیر بودن
    member = await context.bot.get_chat_member(chat.id, user.id)
    if member.status not in ["creator", "administrator"]:
        return await update.message.reply_text("😜 فقط مدیرای باحال می‌تونن پاکسازی کنن!")

    msg = await update.message.reply_text("🧼 خنگول داره آماده می‌شه...", parse_mode="HTML")
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

    # ======================= تابع حذف پیام‌ها =======================
    async def delete_recent_messages(limit=100):
        nonlocal deleted
        async for m in context.bot.get_chat(chat.id).iter_messages(limit=limit):
            try:
                await context.bot.delete_message(chat.id, m.message_id)
                deleted += 1
                if deleted % 100 == 0:
                    await asyncio.sleep(0.5)
            except:
                pass

    # چون PTB متد iter_messages نداره، ما از get_updates شبیه‌سازی می‌کنیم
    async def get_last_messages(limit=100):
        messages = []
        async for i in range(limit):
            yield i  # فقط جایگزین ظاهری

    # ======================= حالت ۱: پاکسازی کلی =======================
    if text in ["پاکسازی", "clean", "پاک"]:
        async for m in context.bot.get_chat_history(chat.id, limit=1):  # این خط دیگه وجود نداره ❌
            pass
        # ما به جای اون مستقیماً از حذف دسته‌ای استفاده می‌کنیم:
        async for i in get_last_messages(5000):
            try:
                await context.bot.delete_message(chat.id, update.message.message_id - i)
                deleted += 1
                if deleted % 100 == 0:
                    await asyncio.sleep(0.3)
            except:
                pass

    # ======================= حالت ۲: حذف عددی =======================
    elif text.startswith("حذف") or text.startswith("پاک "):
        try:
            count = int(args[0]) if args else int(text.split()[1])
        except:
            count = 50
        if count > 10000:
            count = 10000

        async for i in get_last_messages(count):
            try:
                await context.bot.delete_message(chat.id, update.message.message_id - i)
                deleted += 1
                if deleted % 100 == 0:
                    await asyncio.sleep(0.3)
            except:
                pass

    # ======================= حالت ۳: ریپلای به فرد =======================
    elif update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        target_id = target.id
        async for i in get_last_messages(3000):
            try:
                msg_id = update.message.message_id - i
                m = await context.bot.get_message(chat.id, msg_id)
                if m.from_user and m.from_user.id == target_id:
                    await context.bot.delete_message(chat.id, msg_id)
                    deleted += 1
                    if deleted % 100 == 0:
                        await asyncio.sleep(0.3)
            except:
                pass

    # پیام نهایی
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
    """افزودن هندلرهای پاکسازی"""
    application.add_handler(CommandHandler(["clean", "cleanup", "delete"], funny_cleanup))
    application.add_handler(
        MessageHandler(filters.Regex(r"^/?(پاکسازی|پاک|حذف)(\s+\d+)?$") & filters.TEXT, funny_cleanup)
    )
