import asyncio
import json, os
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


# 📂 فایل ذخیره اعضا (برای حالت پرایوسی روشن)
MEMBERS_FILE = "group_members.json"


# 🧠 لود / ذخیره اعضا
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


# 📡 ثبت خودکار کاربران وقتی پیام می‌دن
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


# 📋 منوی تگ پیشرفته
async def handle_tag_menu(update, context):
    keyboard = [
        [InlineKeyboardButton("👑 تگ کاربران مقام‌دار (ادمین)", callback_data="tag_admins")],
        [InlineKeyboardButton("🔥 تگ 50 کاربر فعال اخیر", callback_data="tag_active50")],
        [InlineKeyboardButton("👥 تگ تمام اعضا (حداکثر 300)", callback_data="tag_all300")],
        [InlineKeyboardButton("❌ بستن منو", callback_data="tag_close")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "• حالت تگ کردن را انتخاب کنید :",
        reply_markup=markup,
        parse_mode="HTML"
    )


# 🎯 کال‌بک منو
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
        # 👑 مدیران گروه
        if data == "tag_admins":
            admins = await context.bot.get_chat_administrators(chat.id)
            targets = [a.user for a in admins if not a.user.is_bot]
            title = "کاربران مقام‌دار"

        # 🔥 کاربران فعال اخیر
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
            # مرتب‌سازی از جدیدترین به قدیمی‌تر
            recent.sort(key=lambda x: x[2], reverse=True)
            for uid, name, _ in recent[:50]:
                targets.append({"id": int(uid), "name": name})
            title = "۵۰ کاربر فعال اخیر"

        # 👥 همه کاربران (تا ۳۰۰ نفر)
        elif data == "tag_all300":
            for i, (uid, info) in enumerate(members_data.items()):
                if i >= 300:
                    break
                targets.append({"id": int(uid), "name": info["name"]})
            title = "۳۰۰ عضو گروه"

    except Exception as e:
        return await query.edit_message_text(f"⚠️ خطا در دریافت اطلاعات:\n{e}")

    if not targets:
        return await query.edit_message_text("⚠️ هیچ کاربری برای تگ پیدا نشد!")

    await query.edit_message_text(f"📢 شروع تگ {title} ...")

    batch, count = [], 0
    total = len(targets)

    # 🚀 ارسال مرحله‌ای
    for i, user in enumerate(targets, 1):
        tag = f"<a href='tg://user?id={user['id']}'>{user['name']}</a>"
        batch.append(tag)

        if len(batch) >= 5 or i == total:
            try:
                await context.bot.send_message(chat.id, " ".join(batch), parse_mode="HTML")
                count += len(batch)
                batch = []
                await asyncio.sleep(1.5)
            except Exception as e:
                print(f"⚠️ خطا در ارسال تگ: {e}")

        if i % 50 == 0:
            await asyncio.sleep(5)
            await context.bot.send_message(chat.id, f"⏳ ادامه تگ... ({i}/{total})", parse_mode="HTML")

    await context.bot.send_message(chat.id, f"✅ {count} کاربر {title} تگ شدند.", parse_mode="HTML")
