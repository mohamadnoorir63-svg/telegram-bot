import os
import json
import asyncio
from datetime import datetime, timedelta

import jdatetime
from telegram import Update
from telegram.ext import ContextTypes

# ================= تنظیمات =================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATS_FILE = os.path.join(BASE_DIR, "advanced_stats.json")

SUDO_ID = 8588347189
SAVE_INTERVAL = 300

stats = {}
save_queue = set()
name_cache = {}


# ================= فایل =================

def load_stats():
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ خطا در خواندن آمار: {e}")
    return {}


def save_stats(data):
    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ خطا در ذخیره آمار: {e}")


stats = load_stats()


async def periodic_save():
    while True:
        await asyncio.sleep(SAVE_INTERVAL)

        if save_queue:
            save_stats(stats)
            save_queue.clear()
            print("💾 آمار ذخیره شد")


async def auto_delete(bot, chat_id, message_id, delay=15):
    try:
        await asyncio.sleep(delay)
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass


# ================= روز جدید =================

def init_daily_stats(chat_id, today):
    if chat_id not in stats:
        stats[chat_id] = {}

    if today not in stats[chat_id]:
        stats[chat_id][today] = {
            "messages": {},
            "forwards": 0,
            "videos": 0,
            "video_notes": 0,
            "audios": 0,
            "voices": 0,
            "photos": 0,
            "animations": 0,
            "stickers": 0,
            "animated_stickers": 0,
            "links": 0,
            "mentions": 0,
            "hashtags": 0,
            "replies": 0,
            "files": 0,
            "joins_link": 0,
            "joins_added": 0,
            "lefts": 0,
            "joins_added_per_user": {}
        }


# ================= ابزار نام کاربر =================

async def get_user_name(context, chat_id, user_id):
    key = f"{chat_id}:{user_id}"

    if key in name_cache:
        return name_cache[key]

    try:
        member = await context.bot.get_chat_member(
            int(chat_id),
            int(user_id)
        )
        name = member.user.first_name or "کاربر"
    except Exception:
        name = "کاربر ناشناس"

    name_cache[key] = name
    return name


async def is_admin_or_sudo(context, chat_id, user_id):
    if user_id == SUDO_ID:
        return True

    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ["creator", "administrator"]
    except Exception:
        return False


# ================= ثبت پیام =================

async def record_message_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    if update.effective_chat.type not in ["group", "supergroup"]:
        return

    chat_id = str(update.effective_chat.id)
    user = update.effective_user

    if not user or user.is_bot:
        return

    today = datetime.now().strftime("%Y-%m-%d")
    init_daily_stats(chat_id, today)

    data = stats[chat_id][today]
    msg = update.message

    uid = str(user.id)

    data["messages"][uid] = data["messages"].get(uid, 0) + 1

    if msg.forward_from or msg.forward_from_chat:
        data["forwards"] += 1

    if msg.video:
        data["videos"] += 1
    elif msg.video_note:
        data["video_notes"] += 1
    elif msg.audio:
        data["audios"] += 1
    elif msg.voice:
        data["voices"] += 1
    elif msg.photo:
        data["photos"] += 1
    elif msg.animation:
        data["animations"] += 1
    elif msg.document:
        data["files"] += 1
    elif msg.sticker:
        if getattr(msg.sticker, "is_animated", False):
            data["animated_stickers"] += 1
        else:
            data["stickers"] += 1

    if msg.entities:
        for entity in msg.entities:
            if entity.type == "url":
                data["links"] += 1
            elif entity.type == "mention":
                data["mentions"] += 1
            elif entity.type == "hashtag":
                data["hashtags"] += 1

    if msg.reply_to_message:
        data["replies"] += 1

    save_queue.add(chat_id)


# ================= ورود اعضا =================

async def record_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    if not getattr(update.message, "new_chat_members", None):
        return

    chat_id = str(update.effective_chat.id)
    today = datetime.now().strftime("%Y-%m-%d")

    init_daily_stats(chat_id, today)
    data = stats[chat_id][today]

    for member in update.message.new_chat_members:
        if member.is_bot:
            continue

        if update.message.from_user and update.message.from_user.id != member.id:
            data["joins_added"] += 1

            adder_id = str(update.message.from_user.id)
            data["joins_added_per_user"][adder_id] = (
                data["joins_added_per_user"].get(adder_id, 0) + 1
            )
        else:
            data["joins_link"] += 1

    save_queue.add(chat_id)


# ================= خروج اعضا =================

async def record_left_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    if not getattr(update.message, "left_chat_member", None):
        return

    chat_id = str(update.effective_chat.id)
    today = datetime.now().strftime("%Y-%m-%d")

    init_daily_stats(chat_id, today)

    stats[chat_id][today]["lefts"] += 1
    save_queue.add(chat_id)


# ================= اطلاعات کاربر =================

async def show_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.effective_user
    chat = update.effective_chat
    chat_id = str(chat.id)

    if not await is_admin_or_sudo(context, chat.id, user.id):
        return

    target = (
        update.message.reply_to_message.from_user
        if update.message.reply_to_message
        else user
    )

    today = datetime.now().strftime("%Y-%m-%d")
    jalali_date = jdatetime.datetime.now().strftime("%A %d %B %Y")
    time_str = datetime.now().strftime("%H:%M:%S")

    if target.id == SUDO_ID:
        role = "💎 سودو"
    else:
        try:
            member = await context.bot.get_chat_member(chat.id, target.id)

            if member.status == "creator":
                role = "👑 مالک"
            elif member.status == "administrator":
                role = "🛡️ مدیر"
            else:
                role = "👤 عضو عادی"
        except Exception:
            role = "👤 عضو عادی"

    total_messages = 0
    total_added = 0

    if chat_id in stats and today in stats[chat_id]:
        day_data = stats[chat_id][today]
        total_messages = day_data["messages"].get(str(target.id), 0)
        total_added = day_data["joins_added_per_user"].get(str(target.id), 0)

    username = f"@{target.username}" if target.username else "---"
    user_link = f"<a href='tg://user?id={target.id}'>{target.first_name}</a>"

    text = (
        f"🧿 <b>اطلاعات کاربر:</b>\n\n"
        f"👤 نام: {user_link}\n"
        f"💬 یوزرنیم: {username}\n"
        f"🆔 آیدی عددی: <code>{target.id}</code>\n"
        f"🎖 مقام: {role}\n"
        f"📊 پیام امروز: {total_messages}\n"
        f"📌 اد امروز: {total_added}\n"
        f"📆 تاریخ: {jalali_date}\n"
        f"🕒 ساعت: {time_str}\n"
        f"🆔 آیدی گروه: <code>{chat_id}</code>"
    )

    msg = await update.message.reply_text(text, parse_mode="HTML")
    asyncio.create_task(auto_delete(context.bot, chat.id, msg.message_id, 15))


# ================= آمار گروه سریع بدون عکس =================

async def show_group_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.effective_user
    chat = update.effective_chat
    chat_id = str(chat.id)

    if not await is_admin_or_sudo(context, chat.id, user.id):
        return

    today = datetime.now().strftime("%Y-%m-%d")

    if chat_id not in stats or today not in stats[chat_id]:
        msg = await update.message.reply_text("ℹ️ هنوز فعالیتی برای امروز ثبت نشده است.")
        asyncio.create_task(auto_delete(context.bot, chat.id, msg.message_id, 15))
        return

    data = stats[chat_id][today]

    total_messages = sum(data["messages"].values())
    text_messages = total_messages - (
        data["forwards"]
        + data["videos"]
        + data["video_notes"]
        + data["audios"]
        + data["voices"]
        + data["photos"]
        + data["animations"]
        + data["stickers"]
        + data["animated_stickers"]
        + data["files"]
    )

    if text_messages < 0:
        text_messages = 0

    now = datetime.now()
    time_str = now.strftime("%H:%M:%S")
    jalali_date = jdatetime.datetime.now().strftime("%A %d %B %Y")

    medals = ["🥇", "🥈", "🥉", "🏅", "🏅"]

    top_today = sorted(
        data["messages"].items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]

    top_today_text = ""

    for i, (uid, count) in enumerate(top_today, 1):
        name = await get_user_name(context, chat_id, uid)
        medal = medals[i - 1] if i <= len(medals) else "🏅"
        top_today_text += f"◂ نفر {i} {medal}: {count} پیام | {name}\n"

    if not top_today_text:
        top_today_text = "◂ اطلاعاتی یافت نشد.\n"

    top_adders = sorted(
        data["joins_added_per_user"].items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]

    top_adders_text = ""

    for i, (uid, count) in enumerate(top_adders, 1):
        name = await get_user_name(context, chat_id, uid)
        medal = medals[i - 1] if i <= len(medals) else "🏅"
        top_adders_text += f"◂ نفر {i} {medal}: {count} اد | {name}\n"

    if not top_adders_text:
        top_adders_text = "◂ اطلاعاتی یافت نشد.\n"

    stats_text = f"""
◄ آمار فعالیت گروه از 00:00 تا این لحظه
• تاریخ: {jalali_date}
• ساعت: {time_str}

─┅━ پیام‌های امروز ━┅─
◂ کل پیام‌ها: {total_messages}
◂ متن: {text_messages}
◂ فورواردی: {data["forwards"]}
◂ استیکر: {data["stickers"]}
◂ استیکر متحرک: {data["animated_stickers"]}
◂ گیف: {data["animations"]}
◂ عکس: {data["photos"]}
◂ ویس: {data["voices"]}
◂ موزیک: {data["audios"]}
◂ فیلم: {data["videos"]}
◂ فیلم سلفی: {data["video_notes"]}
◂ فایل: {data["files"]}
◂ لینک: {data["links"]}
◂ منشن: {data["mentions"]}
◂ هشتگ: {data["hashtags"]}
◂ ریپلای: {data["replies"]}

─┅━ ورود و خروج ━┅─
◂ ورود با لینک: {data["joins_link"]}
◂ اضافه‌شده توسط اعضا: {data["joins_added"]}
◂ خروجی: {data["lefts"]}

─┅━ فعال‌ترین‌های امروز ━┅─
{top_today_text}
─┅━ بهترین عضوکننده‌های امروز ━┅─
{top_adders_text}
"""

    msg = await update.message.reply_text(stats_text)
    asyncio.create_task(auto_delete(context.bot, chat.id, msg.message_id, 20))


# ================= آمار شبانه =================

async def send_nightly_stats(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")

    for chat_id, days in list(stats.items()):
        if yesterday not in days:
            continue

        data = days[yesterday]
        total_msgs = sum(data["messages"].values())

        report = (
            f"🌙 آمار شب گذشته ({yesterday})\n\n"
            f"📩 کل پیام‌ها: {total_msgs}\n"
            f"👥 اعضای اضافه‌شده: {data['joins_added']}\n"
            f"🔗 ورود با لینک: {data['joins_link']}\n"
            f"🚪 اعضای خارج‌شده: {data['lefts']}"
        )

        try:
            await context.bot.send_message(chat_id=int(chat_id), text=report)
        except Exception as e:
            print(f"Error sending nightly stats to {chat_id}: {e}")

    for chat_id in list(stats.keys()):
        stats[chat_id] = {}

    save_stats(stats)
    print("🧹 آمار پاکسازی شد ✅")
