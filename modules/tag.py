import asyncio
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

# 📋 منوی انتخاب نوع تگ
async def handle_tag_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("👑 تگ مدیران", callback_data="tag_admins")],
        [InlineKeyboardButton("🔥 تگ فعال‌ها", callback_data="tag_active")],
        [InlineKeyboardButton("👥 تگ همه کاربران", callback_data="tag_all")],
        [InlineKeyboardButton("❌ بستن", callback_data="tag_close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📣 یکی از حالت‌های تگ رو انتخاب کن:", reply_markup=reply_markup)


# 📍 عملکرد تگ‌ها
async def tag_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat = update.effective_chat
    data = query.data

    if data == "tag_close":
        await query.edit_message_text("❌ منوی تگ بسته شد.")
        return

    title = ""
    targets = []

    # 👑 تگ مدیران
    if data == "tag_admins":
        try:
            admins = await context.bot.get_chat_administrators(chat.id)
            targets = [a.user for a in admins if not a.user.is_bot]
            title = "مدیران گروه"
        except Exception as e:
            return await query.edit_message_text(f"⚠️ خطا در دریافت مدیران: {e}")

    # 🔥 تگ کاربران فعال
    elif data == "tag_active":
        title = "کاربران فعال"
        try:
            members = []
            async for member in context.bot.get_chat_administrators(chat.id):
                if not member.user.is_bot:
                    members.append(member.user)

            # چون تلگرام API مستقیمی برای active users نداره، فرض می‌کنیم کاربران اخیر چت فعالن
            recent = []
            async for m in context.bot.get_chat_administrators(chat.id):
                if not m.user.is_bot:
                    recent.append(m.user)

            targets = recent
        except Exception as e:
            return await query.edit_message_text(f"⚠️ خطا در گرفتن کاربران فعال: {e}")

    # 👥 تگ همه کاربران
    elif data == "tag_all":
        title = "همه کاربران"
        try:
            members = []
            async for member in context.bot.get_chat_administrators(chat.id):
                if not member.user.is_bot:
                    members.append(member.user)

            # حالا همه اعضای گروه (اگر ربات ادمین باشه)
            async for member in context.bot.get_chat_administrators(chat.id):
                if not member.user.is_bot:
                    members.append(member.user)
            targets = members
        except Exception as e:
            return await query.edit_message_text(f"⚠️ خطا در دریافت اعضا: {e}")

    if not targets:
        return await query.edit_message_text("⚠️ هیچ کاربری برای تگ پیدا نشد یا ربات دسترسی کافی ندارد.")

    await query.edit_message_text(f"📢 شروع تگ {title} ...")

    # 🧩 تگ کاربران به صورت گروهی
    batch = []
    count = 0
    for i, user in enumerate(targets, 1):
        try:
            tag = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
            batch.append(tag)
            if len(batch) >= 5 or i == len(targets):
                msg = " ".join(batch)
                await context.bot.send_message(chat.id, msg, parse_mode="HTML")
                count += len(batch)
                batch.clear()
                await asyncio.sleep(1)
        except Exception as e:
            print(f"⚠️ خطا در تگ {user.id}: {e}")
            continue

    await context.bot.send_message(chat.id, f"✅ {count} کاربر {title} تگ شدند.", parse_mode="HTML")
