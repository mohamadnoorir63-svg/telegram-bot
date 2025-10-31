
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler
from datetime import datetime, timedelta
import asyncio

# 📍 ساخت منوی انتخاب تگ
async def handle_tag_menu(update, context):
    keyboard = [
        [InlineKeyboardButton("👑 تگ مدیران", callback_data="tag_admins")],
        [InlineKeyboardButton("🔥 تگ فعال‌ها", callback_data="tag_active")],
        [InlineKeyboardButton("👥 تگ 50 کاربر", callback_data="tag_50")],
        [InlineKeyboardButton("👥 تگ 300 کاربر", callback_data="tag_300")],
        [InlineKeyboardButton("❌ بستن", callback_data="tag_close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📣 حالت تگ کردن را انتخاب کنید:", reply_markup=reply_markup)

# 📍 اجرای تگ بر اساس انتخاب
async def tag_callback(update, context):
    query = update.callback_query
    await query.answer()
    chat = update.effective_chat
    data = query.data

    # اگر کاربر بست
    if data == "tag_close":
        await query.edit_message_text("❌ منوی تگ بسته شد.")
        return

    # دریافت اعضا
    try:
        admins = [a.user async for a in context.bot.get_chat_administrators(chat.id)]
        members = [m.user async for m in context.bot.get_chat_members(chat.id)]
    except Exception as e:
        return await query.edit_message_text(f"⚠️ خطا در دریافت اعضا: {e}")

    # نوع تگ
    if data == "tag_admins":
        targets = [u for u in admins if not u.is_bot]
        title = "مدیران گروه"
    elif data == "tag_active":
        # برای تگ فعال‌ها (۳ روز اخیر)
        now = datetime.now()
        threshold = now - timedelta(days=3)
        # اینجا فرض می‌کنیم که دیتابیس فعالیت داری → اگر نداری همه اعضا رو می‌گیره
        try:
            from data.groups import origins_db
            active_data = origins_db.get(str(chat.id), {}).get("users", {})
            targets = [u for u in members if str(u.id) in active_data and datetime.fromisoformat(active_data[str(u.id)]) >= threshold]
        except:
            targets = [u for u in members if not u.is_bot][:50]
        title = "کاربران فعال (۳ روز اخیر)"
    elif data == "tag_50":
        targets = [u for u in members if not u.is_bot][:50]
        title = "۵۰ کاربر اول گروه"
    elif data == "tag_300":
        targets = [u for u in members if not u.is_bot][:300]
        title = "۳۰۰ کاربر گروه"
    else:
        targets = []
        title = "کاربران"

    if not targets:
        await query.edit_message_text("⚠️ هیچ کاربری برای تگ وجود ندارد.")
        return

    await query.edit_message_text(f"📢 شروع تگ {title} ...")

    # تگ‌کردن مرحله‌ای
    batch = []
    count = 0
    for i, user in enumerate(targets, 1):
        if user.is_bot:
            continue
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
                print(f"❌ خطا در ارسال: {e}")

    await context.bot.send_message(chat.id, f"✅ {count} کاربر {title} تگ شدند.", parse_mode="HTML")
