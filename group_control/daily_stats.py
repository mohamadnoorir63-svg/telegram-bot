# ======================= 📊 سیستم آمار و آیدی خنگول فارسی =======================

import os
import json
from datetime import datetime, timedelta
import jdatetime
from telegram import Update
from telegram.ext import ContextTypes

# 📁 فایل ذخیره آمار
STATS_FILE = "daily_stats.json"
SUDO_ID = 7089376754  # 👈 آیدی سودو خودت

# ======================= 💾 بارگذاری و ذخیره =======================
def load_stats():
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ خطا در خواندن daily_stats.json: {e}")
    return {}

def save_stats(data):
    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ خطا در ذخیره daily_stats.json: {e}")

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

    uid = str(user.id)
    data["messages"][uid] = data["messages"].get(uid, 0) + 1
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

# ======================= 📊 نمایش آمار و آیدی =======================
async def show_daily_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = str(update.effective_chat.id)
        user = update.effective_user
        today = datetime.now().strftime("%Y-%m-%d")
        text_input = update.message.text.strip().lower()

        # 📌 آیدی
        if text_input in ["آیدی", "id"]:
            jalali_date = jdatetime.datetime.now().strftime("%A %d %B %Y")
            time_str = datetime.now().strftime("%H:%M:%S")
            user_link = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
            text = (
                f"🧿 <b>اطلاعات شما:</b>\n\n"
                f"👤 {user_link}\n"
                f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
                f"💬 <b>گروه:</b> {update.effective_chat.title}\n"
                f"🏷 <b>Chat ID:</b> <code>{chat_id}</code>\n"
                f"📆 <b>تاریخ:</b> {jalali_date}\n"
                f"🕒 <b>ساعت:</b> {time_str}"
            )
            await update.message.reply_text(text, parse_mode="HTML")
            return

        # 📊 آمار روزانه
        if chat_id not in stats or today not in stats[chat_id]:
            return await update.message.reply_text("ℹ️ هنوز فعالیتی برای امروز ثبت نشده است.")

        data = stats[chat_id][today]
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        jalali_date = jdatetime.datetime.now().strftime("%A %d %B %Y")

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
        )

        if top_user_id:
            text += (
                f"🥇 <b>فعال‌ترین عضو:</b>\n"
                f"👤 <a href='tg://user?id={top_user_id}'>{top_name}</a>\n"
                f"📩 ({top_user_count} پیام)\n\n"
            )

        text += (
            f"✧ <b>اعضای وارد شده با لینک :</b> {data['joins_link']}\n"
            f"✧ <b>اعضای اد شده :</b> {data['joins_added']}\n"
            f"✧ <b>اعضای لفت داده :</b> {data['lefts']}\n"
        )

        await update.message.reply_text(text, parse_mode="HTML")

    except Exception as e:
        print(f"⚠️ خطا در show_daily_stats: {e}")

# ======================= 🌙 آمار شبانه خودکار =======================
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

    for chat_id in list(stats.keys()):
        stats[chat_id] = {}
    save_stats(stats)
    print("🧹 آمار روز گذشته پاک شد ✅")
