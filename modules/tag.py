from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import asyncio
from datetime import datetime, timedelta

# 📍 منوی انتخاب نوع تگ
async def handle_tag_menu(update, context):
    keyboard = [
        [InlineKeyboardButton("👑 تگ مدیران", callback_data="tag_admins")],
        [InlineKeyboardButton("🔥 تگ فعال‌ها", callback_data="tag_active")],
        [InlineKeyboardButton("👥 تگ 50 کاربر", callback_data="tag_50")],
        [InlineKeyboardButton("👥 تگ 300 کاربر", callback_data="tag_300")],
        [InlineKeyboardButton("❌ بستن", callback_data="tag_close")],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📣 حالت تگ کردن را انتخاب کنید:", reply_markup=markup)


# 📍 پاسخ به دکمه‌های تگ
async def tag_callback(update, context):
    query = update.callback_query
    chat = update.effective_chat
    data = query.data
    await query.answer()

    # بستن منو
    if data == "tag_close":
        return await query.edit_message_text("❌ منوی تگ بسته شد.")

    # دریافت مدیران (مجاز در API)
    try:
        admins = await context.bot.get_chat_administrators(chat.id)
    except Exception as e:
        return await query.edit_message_text(f"⚠️ خطا در دریافت مدیران: {e}")

    # 🧩 نوع تگ
    if data == "tag_admins":
        targets = [a.user for a in admins if not a.user.is_bot]
        title = "مدیران گروه"

    elif data == "tag_active":
        # برای تست چون دیتابیس نداریم → تگ همان مدیران
        targets = [a.user for a in admins if not a.user.is_bot]
        title = "کاربران فعال (شبیه‌سازی)"
    elif data == "tag_50":
        targets = [a.user for a in admins if not a.user.is_bot]
        title = "۵۰ کاربر اول (در نسخه رسمی فقط مدیران قابل خواندن‌اند)"
    elif data == "tag_300":
        targets = [a.user for a in admins if not a.user.is_bot]
        title = "۳۰۰ کاربر گروه (در نسخه رسمی فقط مدیران قابل خواندن‌اند)"
    else:
        targets = []
        title = "کاربران"

    if not targets:
        return await query.edit_message_text("⚠️ هیچ کاربری برای تگ وجود ندارد.")

    await query.edit_message_text(f"📢 شروع تگ {title} ...")

    # تگ کردن به‌صورت گروهی
    batch = []
    count = 0
    for i, user in enumerate(targets, 1):
        if user.username:
            tag = f"@{user.username}"
        else:
            tag = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
        batch.append(tag)

        if len(batch) >= 5 or i == len(targets):
            try:
                await context.bot.send_message(chat.id, " ".join(batch), parse_mode="HTML")
                count += len(batch)
                batch = []
                await asyncio.sleep(1)
            except Exception as e:
                print(f"❌ خطا در ارسال تگ: {e}")

    await context.bot.send_message(chat.id, f"✅ {count} کاربر {title} تگ شدند.", parse_mode="HTML")
