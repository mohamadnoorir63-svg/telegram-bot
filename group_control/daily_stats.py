# ======================= 📊 سیستم آمار پیشرفته تلگرام =======================

import os
import json
import asyncio
from datetime import datetime, timedelta
import jdatetime
from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes
import matplotlib.pyplot as plt

# ------------------- تنظیمات -------------------
STATS_FILE = "advanced_stats.json"
SUDO_ID = 7089376754  # آیدی سودو شما
SAVE_INTERVAL = 300  # ذخیره هر 5 دقیقه (ثانیه)

# ------------------- بارگذاری و ذخیره -------------------
def load_stats():
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ خطا در خواندن {STATS_FILE}: {e}")
    return {}

def save_stats(data):
    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ خطا در ذخیره {STATS_FILE}: {e}")

stats = load_stats()
save_queue = set()  # صف گروه‌هایی که نیاز به ذخیره دارند

async def periodic_save():
    while True:
        await asyncio.sleep(SAVE_INTERVAL)
        if save_queue:
            save_stats(stats)
            save_queue.clear()
            print("💾 آمار ذخیره شد (save_queue)")

# ------------------- ایجاد روز جدید -------------------
def init_daily_stats(chat_id, today):
    if chat_id not in stats:
        stats[chat_id] = {}
    if today not in stats[chat_id]:
        stats[chat_id][today] = {
            "messages": {}, "forwards": 0, "videos": 0, "video_notes": 0,
            "audios": 0, "voices": 0, "photos": 0, "animations": 0,
            "stickers": 0, "animated_stickers": 0,
            "links": 0, "mentions": 0, "hashtags": 0,
            "replies": 0, "message_length": {},
            "joins_link": 0, "joins_added": 0,
            "lefts": 0, "kicked": 0, "muted": 0
        }

# ------------------- ثبت فعالیت پیام -------------------
async def record_message_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or update.effective_chat.type not in ["group", "supergroup"]:
        return

    chat_id = str(update.effective_chat.id)
    user = update.effective_user
    today = datetime.now().strftime("%Y-%m-%d")

    init_daily_stats(chat_id, today)
    data = stats[chat_id][today]
    msg = update.message

    # نوع پیام
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

    # لینک، منشن، هشتگ
    if msg.entities:
        for entity in msg.entities:
            if entity.type == "url":
                data["links"] += 1
            elif entity.type == "mention":
                data["mentions"] += 1
            elif entity.type == "hashtag":
                data["hashtags"] += 1

    # ریپلای
    if msg.reply_to_message:
        data["replies"] += 1

    # تعداد پیام‌ها و طول پیام
    uid = str(user.id)
    data["messages"][uid] = data["messages"].get(uid, 0) + 1
    data["message_length"][uid] = data["message_length"].get(uid, 0) + len(msg.text or "")

    save_queue.add(chat_id)

# ------------------- ثبت ورود اعضا -------------------
async def record_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.new_chat_members:
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
        else:
            data["joins_link"] += 1

    save_queue.add(chat_id)

# ------------------- ثبت خروج اعضا -------------------
async def record_left_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.left_chat_member:
        return

    chat_id = str(update.effective_chat.id)
    today = datetime.now().strftime("%Y-%m-%d")
    init_daily_stats(chat_id, today)

    stats[chat_id][today]["lefts"] += 1
    save_queue.add(chat_id)

# ------------------- نمایش آمار پیشرفته -------------------
async def show_daily_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = str(update.effective_chat.id)
        user = update.effective_user
        today = datetime.now().strftime("%Y-%m-%d")
        text_input = update.message.text.strip().lower()

        # 🔒 بررسی دسترسی
        if user.id != SUDO_ID:
            try:
                member = await context.bot.get_chat_member(chat_id, user.id)
                if member.status not in ["creator", "administrator"]:
                    msg = await update.message.reply_text("🚫 فقط مدیران یا سودو مجاز هستند.")
                    await asyncio.sleep(10)
                    await context.bot.delete_message(chat_id, msg.message_id)
                    return
            except:
                return

        # حالت آیدی
        if text_input in ["آیدی", "id"]:
            target = update.message.reply_to_message.from_user if update.message.reply_to_message else user
            jalali_date = jdatetime.datetime.now().strftime("%A %d %B %Y")
            time_str = datetime.now().strftime("%H:%M:%S")
            user_link = f"<a href='tg://user?id={target.id}'>{target.first_name}</a>"
            text = (
                f"🧿 <b>اطلاعات کاربر:</b>\n\n"
                f"👤 {user_link}\n"
                f"🆔 <b>ID:</b> <code>{target.id}</code>\n"
                f"💬 <b>گروه:</b> {update.effective_chat.title}\n"
                f"📆 <b>تاریخ:</b> {jalali_date}\n"
                f"🕒 <b>ساعت:</b> {time_str}"
            )
            try:
                photos = await context.bot.get_user_profile_photos(target.id, limit=1)
                if photos.total_count > 0:
                    photo = photos.photos[0][-1].file_id
                    msg = await context.bot.send_photo(chat_id, photo=photo, caption=text, parse_mode="HTML")
                else:
                    msg = await update.message.reply_text(text, parse_mode="HTML")
                await asyncio.sleep(15)
                await context.bot.delete_message(chat_id, msg.message_id)
            except:
                msg = await update.message.reply_text(text, parse_mode="HTML")
                await asyncio.sleep(15)
                await context.bot.delete_message(chat_id, msg.message_id)
            return

        # نمایش آمار روزانه
        if chat_id not in stats or today not in stats[chat_id]:
            msg = await update.message.reply_text("ℹ️ هنوز فعالیتی برای امروز ثبت نشده است.")
            await asyncio.sleep(15)
            await context.bot.delete_message(chat_id, msg.message_id)
            return

        data = stats[chat_id][today]
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        jalali_date = jdatetime.datetime.now().strftime("%A %d %B %Y")

        # فعال‌ترین کاربر
        if data["messages"]:
            top_user_id = max(data["messages"], key=lambda x: data["messages"][x])
            top_user_count = data["messages"][top_user_id]
            top_name = (await context.bot.get_chat_member(chat_id, top_user_id)).user.first_name
        else:
            top_user_id, top_user_count, top_name = None, 0, "❌ هیچ فعالیتی نیست"

        text = (
            f"♡ <b>فعالیت‌های امروز تا این لحظه :</b>\n"
            f"➲ <b>تاریخ :</b> {jalali_date}\n"
            f"➲ <b>ساعت :</b> {time_str}\n\n"
            f"✛ <b>کل پیام‌ها :</b> {sum(data['messages'].values())}\n"
            f"✛ <b>فیلم :</b> {data['videos']}\n"
            f"✛ <b>عکس :</b> {data['photos']}\n"
            f"✛ <b>گیف :</b> {data['animations']}\n"
            f"✛ <b>ویس :</b> {data['voices']}\n"
            f"✛ <b>آهنگ :</b> {data['audios']}\n"
            f"✛ <b>استیکر :</b> {data['stickers']}\n"
            f"✛ <b>استیکر متحرک :</b> {data['animated_stickers']}\n\n"
            f"✛ <b>لینک‌ها :</b> {data['links']}\n"
            f"✛ <b>منشن‌ها :</b> {data['mentions']}\n"
            f"✛ <b>هشتگ‌ها :</b> {data['hashtags']}\n"
            f"✛ <b>ریپلای‌ها :</b> {data['replies']}\n"
        )

        if top_user_id:
            text += f"🥇 <b>فعال‌ترین عضو:</b> 👤 <a href='tg://user?id={top_user_id}'>{top_name}</a> ({top_user_count} پیام)\n\n"

        text += (
            f"✧ <b>اعضای وارد شده با لینک :</b> {data['joins_link']}\n"
            f"✧ <b>اعضای اد شده :</b> {data['joins_added']}\n"
            f"✧ <b>اعضای لفت داده :</b> {data['lefts']}\n"
        )

        msg = await update.message.reply_text(text, parse_mode="HTML")
        await asyncio.sleep(15)
        await context.bot.delete_message(chat_id, msg.message_id)

    except Exception as e:
        print(f"⚠️ خطا در show_daily_stats: {e}")

# ------------------- آمار شبانه و پاکسازی -------------------
async def send_nightly_stats(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    for chat_id, days in stats.items():
        if yesterday in days:
            data = days[yesterday]
            total_msgs = sum(data["messages"].values())
            report = (
                f"🌙 <b>آمار شب گذشته ({yesterday})</b>\n"
                f"📩 <b>کل پیام‌ها:</b> {total_msgs}\n"
                f"👥 <b>اعضا اضافه‌شده:</b> {data['joins_added']}\n"
                f"🚪 <b>اعضا خارج‌شده:</b> {data['lefts']}"
            )
            try:
                await context.bot.send_message(chat_id, report, parse_mode="HTML")
            except:
                pass
    # پاکسازی آمار قدیمی
    for chat_id in list(stats.keys()):
        stats[chat_id] = {}
    save_stats(stats)
    print("🧹 آمار روز گذشته پاک شد ✅")
