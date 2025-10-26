import os
import json
from datetime import datetime
from hijri_converter import Gregorian
from telegram import Update
from telegram.ext import ContextTypes
import jdatetime  # برای تاریخ شمسی
import aiofiles

STATS_FILE = "daily_stats.json"

def load_stats():
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_stats(data):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

stats = load_stats()

# ======================= 🧠 ثبت فعالیت پیام‌ها =======================
async def record_message_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or update.effective_chat.type not in ["group", "supergroup"]:
        return

    chat_id = str(update.effective_chat.id)
    user = update.effective_user
    today = datetime.now().strftime("%Y-%m-%d")

    if chat_id not in stats:
        stats[chat_id] = {}

    if today not in stats[chat_id]:
        stats[chat_id][today] = {
            "messages": {}, "forwards": 0, "videos": 0, "video_notes": 0,
            "audios": 0, "voices": 0, "photos": 0, "animations": 0,
            "stickers": 0, "animated_stickers": 0,
            "joins_link": 0, "joins_added": 0,
            "lefts": 0, "kicked": 0, "muted": 0
        }

    data = stats[chat_id][today]
    msg = update.message

    # نوع پیام‌ها
    if msg.forward_from or msg.forward_from_chat:
        data["forwards"] += 1
    elif msg.video:
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
    elif msg.sticker:
        if msg.sticker.is_animated:
            data["animated_stickers"] += 1
        else:
            data["stickers"] += 1

    # شمارش پیام‌های کاربر
    data["messages"][str(user.id)] = data["messages"].get(str(user.id), 0) + 1

    save_stats(stats)

# ======================= 👥 ثبت ورود اعضا =======================
async def record_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.new_chat_members:
        return
    chat_id = str(update.effective_chat.id)
    today = datetime.now().strftime("%Y-%m-%d")

    if chat_id not in stats:
        stats[chat_id] = {}

    if today not in stats[chat_id]:
        stats[chat_id][today] = {
            "messages": {}, "forwards": 0, "videos": 0, "video_notes": 0,
            "audios": 0, "voices": 0, "photos": 0, "animations": 0,
            "stickers": 0, "animated_stickers": 0,
            "joins_link": 0, "joins_added": 0,
            "lefts": 0, "kicked": 0, "muted": 0
        }

    data = stats[chat_id][today]
    for member in update.message.new_chat_members:
        # تشخیص ورود با لینک یا اد دستی
        if member.is_bot:
            continue
        if update.message.from_user and update.message.from_user.id != member.id:
            data["joins_added"] += 1
        else:
            data["joins_link"] += 1

    save_stats(stats)

# ======================= 🚪 ثبت خروج اعضا =======================
async def record_left_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.left_chat_member:
        return
    chat_id = str(update.effective_chat.id)
    today = datetime.now().strftime("%Y-%m-%d")

    if chat_id not in stats:
        stats[chat_id] = {}

    if today not in stats[chat_id]:
        stats[chat_id][today] = {
            "messages": {}, "forwards": 0, "videos": 0, "video_notes": 0,
            "audios": 0, "voices": 0, "photos": 0, "animations": 0,
            "stickers": 0, "animated_stickers": 0,
            "joins_link": 0, "joins_added": 0,
            "lefts": 0, "kicked": 0, "muted": 0
        }

    stats[chat_id][today]["lefts"] += 1
    save_stats(stats)

# ======================= 📊 نمایش آمار روزانه فارسی =======================
async def show_daily_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    today = datetime.now().strftime("%Y-%m-%d")

    if chat_id not in stats or today not in stats[chat_id]:
        return await update.message.reply_text("ℹ️ هنوز فعالیتی برای امروز ثبت نشده است.")

    data = stats[chat_id][today]

    # 🕓 زمان و تاریخ فارسی
    now = datetime.now()
    time_str = now.strftime("%H:%M:%S")
    jalali_date = jdatetime.datetime.now().strftime("%A %d %B %Y").replace("202", "۱۴۰")

    # فعال‌ترین کاربر
    if data["messages"]:
        top_user_id = max(data["messages"], key=lambda x: data["messages"][x])
        top_user_count = data["messages"][top_user_id]
        try:
            member = await context.bot.get_chat_member(chat_id, top_user_id)
            top_name = member.user.first_name
        except:
            top_name = "کاربر ناشناس"
    else:
        top_user_id, top_user_count, top_name = None, 0, "❌ هیچ فعالیتی نیست"

    # 📊 قالب نهایی
    text = (
        f"♡ <b>فعالیت‌های امروز تا این لحظه :</b>\n"
        f"➲ <b>تاریخ :</b> {jalali_date}\n"
        f"➲ <b>ساعت :</b> {time_str}\n\n"
        f"✛ <b>کل پیام‌ها :</b> {sum(data['messages'].values())}\n"
        f"✛ <b>پیام فورواردی :</b> {data['forwards']}\n"
        f"✛ <b>فیلم :</b> {data['videos']}\n"
        f"✛ <b>فیلم سلفی :</b> {data['video_notes']}\n"
        f"✛ <b>آهنگ :</b> {data['audios']}\n"
        f"✛ <b>ویس :</b> {data['voices']}\n"
        f"✛ <b>عکس :</b> {data['photos']}\n"
        f"✛ <b>گیف :</b> {data['animations']}\n"
        f"✛ <b>استیکر :</b> {data['stickers']}\n"
        f"✛ <b>استیکر متحرک :</b> {data['animated_stickers']}\n\n"
        f"✶ <b>فعال‌ترین اعضای گروه:</b>\n"
    )

    if top_user_id:
        text += (
            f"• 🥇 نفر اول : <a href='tg://user?id={top_user_id}'>{top_name}</a>\n"
            f"   ( {top_user_count} پیام )\n\n"
        )
    else:
        text += "هیچ پیامی ثبت نشده است.\n\n"

    text += (
        f"✶ <b>کاربران برتر در افزودن عضو :</b>\n"
        f"هیچ فعالیتی ثبت نشده است!\n\n"
        f"✧ <b>اعضای وارد شده با لینک :</b> {data['joins_link']}\n"
        f"✧ <b>اعضای اد شده :</b> {data['joins_added']}\n"
        f"✧ <b>کل اعضای وارد شده :</b> {data['joins_link'] + data['joins_added']}\n"
        f"✧ <b>اعضای اخراج شده :</b> {data['kicked']}\n"
        f"✧ <b>اعضای سکوت شده :</b> {data['muted']}\n"
        f"✧ <b>اعضای لفت داده :</b> {data['lefts']}\n"
    )

    await update.message.reply_text(text, parse_mode="HTML")
