import asyncio
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


# 📋 منوی تگ
async def handle_tag_menu(update, context):
    keyboard = [
        [InlineKeyboardButton("👑 تگ مدیران", callback_data="tag_admins")],
        [InlineKeyboardButton("🔥 تگ فعال‌ها", callback_data="tag_active")],
        [InlineKeyboardButton("👥 تگ همه کاربران", callback_data="tag_all")],
        [InlineKeyboardButton("❌ بستن", callback_data="tag_close")],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📣 یکی از حالت‌های تگ را انتخاب کن:", reply_markup=markup)


# 🎯 عملکرد دکمه‌ها
async def tag_callback(update, context):
    query = update.callback_query
    await query.answer()
    chat = update.effective_chat
    data = query.data

    if data == "tag_close":
        await query.edit_message_text("❌ منوی تگ بسته شد.")
        return

    targets = []
    title = ""

    try:
        # 👑 فقط مدیران
        if data == "tag_admins":
            admins = await context.bot.get_chat_administrators(chat.id)
            targets = [a.user for a in admins if not a.user.is_bot]
            title = "مدیران گروه"

        # 🔥 کاربران فعال (تقریبی، چون API لیست کامل اعضا نمی‌دهد)
        elif data == "tag_active":
            admins = await context.bot.get_chat_administrators(chat.id)
            targets = [a.user for a in admins if not a.user.is_bot]
            title = "کاربران فعال (۳ روز اخیر تقریبی)"

        # 👥 همه کاربران (در دسترس فقط در صورت خاموش بودن پرایوسی‌مد)
        elif data == "tag_all":
            try:
                members = await context.bot.get_chat_member_count(chat.id)
                admins = await context.bot.get_chat_administrators(chat.id)
                targets = [a.user for a in admins if not a.user.is_bot]
                title = f"همه کاربران (نمایشی - {members} نفر)"
            except Exception as e:
                return await query.edit_message_text(f"⚠️ خطا در دریافت اعضا:\n{e}")

    except Exception as e:
        return await query.edit_message_text(f"⚠️ خطا در دریافت اعضای گروه:\n{e}")

    if not targets:
        return await query.edit_message_text("⚠️ هیچ کاربری برای تگ پیدا نشد!")

    await query.edit_message_text(f"📢 شروع تگ {title} ...")

    # 🚀 ارسال دسته‌ای برای جلوگیری از Flood
    batch = []
    count = 0
    for i, user in enumerate(targets, 1):
        tag = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
        batch.append(tag)

        if len(batch) >= 5 or i == len(targets):
            try:
                await context.bot.send_message(chat.id, " ".join(batch), parse_mode="HTML")
                count += len(batch)
                batch = []
                await asyncio.sleep(1.3)
            except Exception as e:
                print(f"⚠️ خطا در ارسال تگ: {e}")

    await context.bot.send_message(chat.id, f"✅ {count} کاربر {title} تگ شدند.", parse_mode="HTML")
