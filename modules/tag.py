import asyncio
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# منوی تگ
async def handle_tag_menu(update, context):
    keyboard = [
        [InlineKeyboardButton("👑 تگ مدیران", callback_data="tag_admins")],
        [InlineKeyboardButton("🔥 تگ فعال‌ها", callback_data="tag_active")],
        [InlineKeyboardButton("👥 تگ همه کاربران (شناخته‌شده)", callback_data="tag_all")],
        [InlineKeyboardButton("❌ بستن", callback_data="tag_close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📣 یکی از حالت‌های تگ رو انتخاب کن:", reply_markup=reply_markup)


# حافظه موقت کاربران دیده‌شده
known_members = {}

# ذخیره هر کاربر که پیام می‌دهد
async def track_member(update, context):
    chat_id = update.effective_chat.id
    user = update.effective_user
    if chat_id not in known_members:
        known_members[chat_id] = {}
    known_members[chat_id][user.id] = {
        "name": user.first_name,
        "last_active": datetime.now().isoformat()
    }


# کال‌بک تگ
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

    if data == "tag_admins":
        try:
            admins = await context.bot.get_chat_administrators(chat.id)
            targets = [a.user for a in admins if not a.user.is_bot]
            title = "مدیران گروه"
        except Exception as e:
            return await query.edit_message_text(f"⚠️ خطا در دریافت مدیران: {e}")

    elif data == "tag_active":
        title = "کاربران فعال (۳ روز اخیر)"
        now = datetime.now()
        three_days_ago = now - timedelta(days=3)
        for uid, info in known_members.get(chat.id, {}).items():
            try:
                if datetime.fromisoformat(info["last_active"]) >= three_days_ago:
                    targets.append({"id": uid, "name": info["name"]})
            except:
                continue

    elif data == "tag_all":
        title = "همه کاربران شناخته‌شده"
        for uid, info in known_members.get(chat.id, {}).items():
            targets.append({"id": uid, "name": info["name"]})

    if not targets:
        return await query.edit_message_text("⚠️ هنوز هیچ کاربری برای تگ شناخته نشده!")

    await query.edit_message_text(f"📢 شروع تگ {title} ...")

    batch, count = [], 0
    for i, user in enumerate(targets, 1):
        tag = f"<a href='tg://user?id={user['id']}'>{user['name']}</a>"
        batch.append(tag)

        if len(batch) >= 5 or i == len(targets):
            try:
                await context.bot.send_message(chat.id, " ".join(batch), parse_mode="HTML")
                count += len(batch)
                batch = []
                await asyncio.sleep(1)
            except Exception as e:
                print(f"⚠️ خطا در ارسال تگ: {e}")

    await context.bot.send_message(chat.id, f"✅ {count} کاربر {title} تگ شدند.", parse_mode="HTML")
