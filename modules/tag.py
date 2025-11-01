import asyncio
import json, os
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# 📂 فایل ذخیره اعضا
MEMBERS_FILE = "group_members.json"


# 🧩 بارگذاری و ذخیره JSON
def load_members():
    if os.path.exists(MEMBERS_FILE):
        try:
            with open(MEMBERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}


def save_members(data):
    with open(MEMBERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# 🧠 دادهٔ سراسری
group_members = load_members()


# 🧩 ثبت هر کاربر که پیام می‌دهد
async def track_member(update, context):
    if not update.message:
        return

    chat_id = str(update.effective_chat.id)
    user = update.effective_user

    if chat_id not in group_members:
        group_members[chat_id] = {}

    group_members[chat_id][str(user.id)] = {
        "name": user.first_name,
        "last_active": datetime.now().isoformat(),
    }
    save_members(group_members)


# 📋 منوی تگ
async def handle_tag_menu(update, context):
    keyboard = [
        [InlineKeyboardButton("👑 تگ مدیران", callback_data="tag_admins")],
        [InlineKeyboardButton("🔥 تگ فعال‌ها", callback_data="tag_active")],
        [InlineKeyboardButton("👥 تگ همه کاربران", callback_data="tag_all")],
        [InlineKeyboardButton("📊 نمایش آمار اعضا", callback_data="tag_stats")],
        [InlineKeyboardButton("❌ بستن", callback_data="tag_close")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📣 یکی از گزینه‌ها را انتخاب کن:", reply_markup=reply_markup)


# 🎯 کال‌بک دکمه‌ها
async def tag_callback(update, context):
    query = update.callback_query
    await query.answer()
    chat = update.effective_chat
    data = query.data
    chat_id = str(chat.id)

    if data == "tag_close":
        await query.edit_message_text("❌ منوی تگ بسته شد.")
        return

    members = group_members.get(chat_id, {})
    targets = []
    title = ""

    # 👑 فقط مدیران
    if data == "tag_admins":
        try:
            admins = await context.bot.get_chat_administrators(chat.id)
            for admin in admins:
                if not admin.user.is_bot:
                    targets.append({"id": admin.user.id, "name": admin.user.first_name})
            title = "مدیران گروه"
        except Exception as e:
            return await query.edit_message_text(f"⚠️ خطا در دریافت مدیران:\n{e}")

    # 🔥 کاربران فعال (۳ روز اخیر)
    elif data == "tag_active":
        now = datetime.now()
        threshold = now - timedelta(days=3)
        for uid, info in members.items():
            try:
                last = datetime.fromisoformat(info["last_active"])
                if last >= threshold:
                    targets.append({"id": int(uid), "name": info["name"]})
            except:
                continue
        title = "کاربران فعال (۳ روز اخیر)"

    # 👥 همه کاربران ذخیره‌شده
    elif data == "tag_all":
        for uid, info in members.items():
            targets.append({"id": int(uid), "name": info["name"]})
        title = "همه کاربران گروه"

    # 📊 آمار اعضا
    elif data == "tag_stats":
        total = len(members)
        active = 0
        now = datetime.now()
        threshold = now - timedelta(days=3)

        for info in members.values():
            try:
                last = datetime.fromisoformat(info["last_active"])
                if last >= threshold:
                    active += 1
            except:
                continue

        try:
            admins = await context.bot.get_chat_administrators(chat.id)
            admin_count = len([a for a in admins if not a.user.is_bot])
        except:
            admin_count = "نامشخص"

        text = (
            f"📊 <b>آمار اعضای گروه:</b>\n\n"
            f"👥 کل اعضای شناخته‌شده: <b>{total}</b>\n"
            f"🔥 فعال در ۳ روز اخیر: <b>{active}</b>\n"
            f"👑 مدیران گروه: <b>{admin_count}</b>\n\n"
            f"🕒 آخرین بروزرسانی: {datetime.now().strftime('%H:%M - %d/%m/%Y')}"
        )

        return await query.edit_message_text(text, parse_mode="HTML")

    # 🧩 بررسی اعضا
    if not targets:
        return await query.edit_message_text("⚠️ هیچ کاربری برای تگ پیدا نشد!")

    await query.edit_message_text(f"📢 شروع تگ {title} ...")

    batch, count, total = [], 0, len(targets)

    # 🚀 تگ مرحله‌ای ضد‌کرش
    for i, user in enumerate(targets, 1):
        tag = f"<a href='tg://user?id={user['id']}'>{user['name']}</a>"
        batch.append(tag)

        if len(batch) >= 5 or i == total:
            try:
                await context.bot.send_message(chat.id, " ".join(batch), parse_mode="HTML")
                count += len(batch)
                batch = []
                await asyncio.sleep(1.2)  # فاصله بین دسته‌ها
            except Exception as e:
                print(f"⚠️ خطا در ارسال تگ: {e}")

        # ⚙️ توقف کوتاه بین ۵۰ پیام برای جلوگیری از ری‌استارت
        if i % 50 == 0:
            await asyncio.sleep(5)
            await context.bot.send_message(chat.id, f"⏳ ادامه تگ... ({i}/{total})", parse_mode="HTML")

    await context.bot.send_message(chat.id, f"✅ {count} کاربر {title} تگ شدند.", parse_mode="HTML")
