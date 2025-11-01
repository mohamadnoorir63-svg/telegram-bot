import asyncio
import json, os
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# 📂 فایل ذخیره اعضا
MEMBERS_FILE = "group_members.json"


# 🧠 لود و ذخیره اطلاعات
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


group_members = load_members()


# 📡 ثبت خودکار کاربران (پیام یا جوین)
async def track_member(update, context):
    user = None
    chat_id = None

    if update.message:
        user = update.effective_user
        chat_id = str(update.effective_chat.id)
    elif update.chat_member:
        user = update.chat_member.new_chat_member.user
        chat_id = str(update.chat_member.chat.id)
    else:
        return

    if not user or user.is_bot:
        return

    if chat_id not in group_members:
        group_members[chat_id] = {}

    group_members[chat_id][str(user.id)] = {
        "name": user.first_name,
        "last_active": datetime.now().isoformat(),
    }

    save_members(group_members)


# 📋 ساخت منوی تگ
async def handle_tag_menu(update, context):
    keyboard = [
        [InlineKeyboardButton("👑 تگ کاربران مقام‌دار (ادمین)", callback_data="tag_admins")],
        [InlineKeyboardButton("🔥 تگ ۵۰ کاربر فعال اخیر", callback_data="tag_active50")],
        [InlineKeyboardButton("👥 تگ تمام اعضا (حداکثر ۳۰۰)", callback_data="tag_all300")],
        [InlineKeyboardButton("❌ بستن منو", callback_data="tag_close")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "• حالت تگ کردن را انتخاب کنید :",
        reply_markup=markup,
        parse_mode="HTML"
    )


# 🎯 کال‌بک دکمه‌ها
async def tag_callback(update, context):
    query = update.callback_query
    await query.answer()
    chat = update.effective_chat
    chat_id = str(chat.id)
    data = query.data

    if data == "tag_close":
        await query.edit_message_text("❌ منوی تگ بسته شد.")
        return

    members_data = group_members.get(chat_id, {})
    targets = []
    title = ""

    try:
        # 👑 مدیران
        if data == "tag_admins":
            admins = await context.bot.get_chat_administrators(chat.id)
            for admin in admins:
                if not admin.user.is_bot:
                    targets.append({"id": admin.user.id, "name": admin.user.first_name})
            title = "کاربران مقام‌دار"

        # 🔥 فعال‌ترین ۵۰ نفر اخیر
        elif data == "tag_active50":
            now = datetime.now()
            threshold = now - timedelta(days=3)
            recent = []
            for uid, info in members_data.items():
                try:
                    last = datetime.fromisoformat(info["last_active"])
                    if last >= threshold:
                        recent.append((uid, info["name"], last))
                except:
                    continue
            recent.sort(key=lambda x: x[2], reverse=True)
            for uid, name, _ in recent[:50]:
                targets.append({"id": int(uid), "name": name})
            title = "۵۰ کاربر فعال اخیر"

        # 👥 همه کاربران (حداکثر ۳۰۰)
        elif data == "tag_all300":
            # از فایل
            for i, (uid, info) in enumerate(members_data.items()):
                if i >= 300:
                    break
                targets.append({"id": int(uid), "name": info["name"]})

            # در صورت نیاز، مدیرها رو هم اضافه کن
            admins = await context.bot.get_chat_administrators(chat.id)
            for a in admins:
                if not a.user.is_bot and a.user.id not in [t["id"] for t in targets]:
                    targets.append({"id": a.user.id, "name": a.user.first_name})

            title = "تمام اعضا (حداکثر ۳۰۰)"

    except Exception as e:
        return await query.edit_message_text(f"⚠️ خطا در دریافت اطلاعات:\n{e}")

    if not targets:
        return await query.edit_message_text("⚠️ هیچ کاربری برای تگ پیدا نشد!")

    await query.edit_message_text(f"📢 شروع تگ {title} ...")

    batch, count = [], 0
    total = len(targets)

    # 🚀 ارسال مرحله‌ای برای جلوگیری از اسپم
    for i, user in enumerate(targets, 1):
        tag = f"<a href='tg://user?id={user['id']}'>{user['name']}</a>"
        batch.append(tag)

        if len(batch) >= 5 or i == total:
            try:
                await context.bot.send_message(chat.id, " ".join(batch), parse_mode="HTML")
                count += len(batch)
                batch = []
                await asyncio.sleep(1.2)
            except Exception as e:
                print(f"⚠️ خطا در ارسال تگ: {e}")

        if i % 50 == 0:
            await asyncio.sleep(5)
            await context.bot.send_message(chat.id, f"⏳ ادامه تگ... ({i}/{total})", parse_mode="HTML")

    await context.bot.send_message(chat.id, f"✅ {count} کاربر {title} تگ شدند.", parse_mode="HTML")
