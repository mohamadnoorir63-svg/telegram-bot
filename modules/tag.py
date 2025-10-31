import asyncio
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

# =========================
# 🎛 منوی انتخاب نوع تگ
# =========================
async def handle_tag_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("👑 تگ مدیران", callback_data="tag_admins")],
        [InlineKeyboardButton("🔥 تگ فعال‌ها (۳ روز اخیر)", callback_data="tag_active")],
        [InlineKeyboardButton("👥 تگ همه کاربران", callback_data="tag_all")],
        [InlineKeyboardButton("❌ بستن", callback_data="tag_close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "📣 یکی از حالت‌های تگ رو انتخاب کن:",
        reply_markup=reply_markup
    )


# =========================
# 📍 عملکرد تگ‌ها
# =========================
async def tag_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat = update.effective_chat
    bot = context.bot
    data = query.data

    if data == "tag_close":
        await query.edit_message_text("❌ منوی تگ بسته شد.")
        return

    title = ""
    targets = []

    # 👑 تگ مدیران
    if data == "tag_admins":
        try:
            admins = await bot.get_chat_administrators(chat.id)
            targets = [a.user for a in admins if not a.user.is_bot]
            title = "مدیران گروه"
        except Exception as e:
            return await query.edit_message_text(f"⚠️ خطا در دریافت مدیران:\n<code>{e}</code>", parse_mode="HTML")

    # 🔥 تگ کاربران فعال
    elif data == "tag_active":
        title = "کاربران فعال (۳ روز اخیر)"
        now = datetime.utcnow()
        threshold = now - timedelta(days=3)
        try:
            members = []
            async for member in bot.get_chat_administrators(chat.id):
                if not member.user.is_bot:
                    members.append(member.user)

            # از API کاربران فعال نداریم، فرض: اعضایی که اخیراً پیام فرستادن
            # از طریق آخرین ۳۰۰ پیام اخیر بررسی می‌کنیم
            active_users = set()
            async for msg in bot.get_chat_history(chat.id, limit=300):
                if msg.from_user and not msg.from_user.is_bot:
                    active_users.add(msg.from_user.id)
            for uid in active_users:
                try:
                    user = await bot.get_chat_member(chat.id, uid)
                    targets.append(user.user)
                except:
                    continue
        except Exception as e:
            return await query.edit_message_text(f"⚠️ خطا در بررسی کاربران فعال:\n<code>{e}</code>", parse_mode="HTML")

    # 👥 تگ همه کاربران
    elif data == "tag_all":
        title = "همه کاربران گروه"
        try:
            async for member in bot.get_chat_members(chat.id, limit=200):
                if not member.user.is_bot:
                    targets.append(member.user)
        except Exception as e:
            return await query.edit_message_text(f"⚠️ خطا در دریافت اعضای گروه:\n<code>{e}</code>", parse_mode="HTML")

    if not targets:
        return await query.edit_message_text("⚠️ هیچ کاربری برای تگ پیدا نشد یا ربات دسترسی کافی ندارد.")

    await query.edit_message_text(f"📢 شروع تگ {title} ... لطفاً صبر کنید.")

    # =========================
    # 🧩 تگ مرحله‌ای با وقفه
    # =========================
    BATCH_SIZE = 5
    count = 0
    batch = []

    for i, user in enumerate(targets, 1):
        tag = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
        batch.append(tag)

        if len(batch) >= BATCH_SIZE or i == len(targets):
            try:
                msg = " ".join(batch)
                await bot.send_message(chat.id, msg, parse_mode="HTML")
                count += len(batch)
                batch.clear()
                await asyncio.sleep(1.5)  # جلوگیری از Flood
            except Exception as e:
                print(f"⚠️ خطا در ارسال تگ: {e}")
                await asyncio.sleep(2)

    await bot.send_message(chat.id, f"✅ {count} کاربر از {title} تگ شدند.", parse_mode="HTML")
