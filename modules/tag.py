import asyncio
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler
from memory_manager import load_data  # 📦 چون همه‌چیز از این تابع خونده میشه

# 📋 منوی انتخاب نوع تگ
async def handle_tag_menu(update, context):
    keyboard = [
        [InlineKeyboardButton("👑 تگ مدیران", callback_data="tag_admins")],
        [InlineKeyboardButton("🔥 تگ فعال‌ها", callback_data="tag_active")],
        [InlineKeyboardButton("👥 تگ همه کاربران", callback_data="tag_all")],
        [InlineKeyboardButton("❌ بستن", callback_data="tag_close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📣 یکی از حالت‌های تگ رو انتخاب کن:", reply_markup=reply_markup)


# 📍 عملکرد تگ‌ها
async def tag_callback(update, context):
    query = update.callback_query
    await query.answer()
    chat = update.effective_chat
    data = query.data

    if data == "tag_close":
        await query.edit_message_text("❌ منوی تگ بسته شد.")
        return

    # 🧩 خواندن اعضای ثبت‌شده از group_data.json
    groups_data = load_data("group_data.json").get("groups", {})
    chat_data = groups_data.get(str(chat.id), {}) if isinstance(groups_data, dict) else None

    members = []
    if chat_data and "members" in chat_data:
        members = chat_data["members"]  # لیست یا دیکشنری کاربران

    targets = []
    title = ""

    # 👑 فقط مدیران
    if data == "tag_admins":
        try:
            admins = await context.bot.get_chat_administrators(chat.id)
            targets = [a.user for a in admins if not a.user.is_bot]
            title = "مدیران گروه"
        except Exception as e:
            return await query.edit_message_text(f"⚠️ خطا در دریافت مدیران: {e}")

    # 🔥 کاربران فعال ۳ روز اخیر
    elif data == "tag_active":
        now = datetime.now()
        threshold = now - timedelta(days=3)
        if isinstance(members, dict):
            for uid, info in members.items():
                try:
                    last = info.get("last_active")
                    if last and datetime.fromisoformat(last) >= threshold:
                        targets.append(int(uid))
                except:
                    continue
        elif isinstance(members, list):
            targets = [m for m in members]  # اگر فقط لیست ساده آیدی باشه
        title = "کاربران فعال (۳ روز اخیر)"

    # 👥 همه کاربران
    elif data == "tag_all":
        if isinstance(members, dict):
            targets = [int(uid) for uid in members.keys()]
        elif isinstance(members, list):
            targets = members
        title = "همه کاربران گروه"

    if not targets:
        return await query.edit_message_text("⚠️ هیچ کاربری برای تگ پیدا نشد.")

    await query.edit_message_text(f"📢 شروع تگ {title} ...")

    batch, count = [], 0
    for i, uid in enumerate(targets, 1):
        tag = f"<a href='tg://user?id={uid}'>👤</a>"
        batch.append(tag)

        # ارسال تگ به صورت دسته‌ای
        if len(batch) >= 5 or i == len(targets):
            try:
                await context.bot.send_message(chat.id, " ".join(batch), parse_mode="HTML")
                count += len(batch)
                batch = []
                await asyncio.sleep(1)
            except Exception as e:
                print(f"⚠️ خطا در ارسال تگ: {e}")

    await context.bot.send_message(chat.id, f"✅ {count} کاربر {title} تگ شدند.", parse_mode="HTML")
