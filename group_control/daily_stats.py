# ======================= 📊 سیستم آمار پیشرفته تلگرام =======================

import os
import json
import asyncio
from datetime import datetime, timedelta
import jdatetime
from telegram import Update
from telegram.ext import ContextTypes

# ------------------- تنظیمات -------------------
STATS_FILE = "advanced_stats.json"
SUDO_ID = 8588347189  # آیدی سودو شما
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
save_queue = set()

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
            "lefts": 0, "kicked": 0, "muted": 0,
            "joins_added_per_user": {}
        }

# ------------------- تابع دریافت اطلاعات ویسکال -------------------
async def get_voice_data(user_id):
    """
    این تابع باید به API واقعی ویسکال یا دیتابیس شما متصل شود.
    برای کاربران معمولی داده پیش‌فرض برمی‌گرداند.
    """
    # داده تستی برای مدیر/سودو
    return {
        "datacenter_code": 5,
        "role": "مالک گروه",
        "time": "05:57:53",
        "percent": "68 %",
        "rank": 6
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
            adder_id = str(update.message.from_user.id)
            data["joins_added_per_user"][adder_id] = data["joins_added_per_user"].get(adder_id, 0) + 1
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

# ------------------- نمایش آمار پیشرفته و آیدی -------------------
async def show_daily_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = str(update.effective_chat.id)
        user = update.effective_user
        today = datetime.now().strftime("%Y-%m-%d")
        text_input = update.message.text.strip().lower()

        # 🔒 بررسی دسترسی
        is_admin = False
        if user.id == SUDO_ID:
            is_admin = True
        else:
            try:
                member = await context.bot.get_chat_member(chat_id, user.id)
                if member.status in ["creator", "administrator"]:
                    is_admin = True
            except:
                pass

        # کاربران غیرمدیر هیچ پاسخی نمی‌بینند
        if not is_admin:
            return

        # ------------------- حالت آیدی پیشرفته -------------------
        if text_input in ["آیدی", "id"]:
            target = update.message.reply_to_message.from_user if update.message.reply_to_message else user

            jalali_date = jdatetime.datetime.now().strftime("%A %d %B %Y")
            time_str = datetime.now().strftime("%H:%M:%S")
            voice_data = await get_voice_data(target.id)

            username = target.username if target.username else "---"
            datacenter_code = voice_data.get("datacenter_code", "---")
            role = voice_data.get("role", "---")
            voice_time = voice_data.get("time", "---")
            voice_percent = voice_data.get("percent", "---")
            voice_rank = voice_data.get("rank", "---")

            user_link = f"<a href='tg://user?id={target.id}'>{target.first_name}</a>"

            text = (
                f"🧿 <b>اطلاعات کاربر:</b>\n\n"
                f"👤 نام: {user_link}\n"
                f"💬 یوزرنیم: {username}\n"
                f"🆔 آیدی عددی: <code>{target.id}</code>\n"
                f"💻 کد دیتاسنتر: {datacenter_code}\n"
                f"🎖 مقام کاربر: {role}\n"
                f"─┅━✦━┅─\n"
                f"◂ زمان حضور در ویسکال: {voice_time}\n"
                f"◂ درصد حضور در ویسکال: {voice_percent}\n"
                f"◂ رتبه حضور در ویسکال: {voice_rank}\n"
                f"📆 تاریخ: {jalali_date}\n"
                f"🕒 ساعت: {time_str}"
            )

            try:
                photos = await context.bot.get_user_profile_photos(target.id, limit=1)
                if photos.total_count > 0:
                    photo = photos.photos[0][-1].file_id
                    msg = await context.bot.send_photo(update.effective_chat.id, photo=photo, caption=text, parse_mode="HTML")
                else:
                    msg = await update.message.reply_text(text, parse_mode="HTML")
            except Exception:
                msg = await update.message.reply_text(text, parse_mode="HTML")

            await asyncio.sleep(15)
            await context.bot.delete_message(update.effective_chat.id, msg.message_id)
            return

        # ------------------- نمایش آمار روزانه -------------------
        if chat_id not in stats or today not in stats[chat_id]:
            msg = await update.message.reply_text("ℹ️ هنوز فعالیتی برای امروز ثبت نشده است.")
            await asyncio.sleep(15)
            await context.bot.delete_message(chat_id, msg.message_id)
            return

        data = stats[chat_id][today]
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        jalali_date = jdatetime.datetime.now().strftime("%A %d %B %Y")

        # نفرات برتر امروز
        top_today = sorted(data["messages"].items(), key=lambda x: x[1], reverse=True)[:3]
        top_today_text = ""
        medals = ["🥇", "🥈", "🥉"]
        for i, (uid, count) in enumerate(top_today, 1):
            try:
                name = (await context.bot.get_chat_member(chat_id, uid)).user.first_name
            except:
                name = "کاربر ناشناس"
            top_today_text += f"◂ نفر {i} {medals[i-1]} :( {count} پیام | {name} )\n"
        if not top_today_text:
            top_today_text = "◂ اطلاعاتی یافت نشد."

        # نفرات برتر کل
        total_msgs_all = {}
        for day_data in stats.get(chat_id, {}).values():
            for uid, count in day_data["messages"].items():
                total_msgs_all[uid] = total_msgs_all.get(uid, 0) + count
        top_all = sorted(total_msgs_all.items(), key=lambda x: x[1], reverse=True)[:3]
        top_all_text = ""
        for i, (uid, count) in enumerate(top_all, 1):
            try:
                name = (await context.bot.get_chat_member(chat_id, uid)).user.first_name
            except:
                name = "کاربر ناشناس"
            top_all_text += f"◂ نفر {i} {medals[i-1]} :( {count} پیام | {name} )\n"
        if not top_all_text:
            top_all_text = "◂ اطلاعاتی یافت نشد."

        # بهترین عضو کننده‌ها
        top_adders = sorted(data["joins_added_per_user"].items(), key=lambda x: x[1], reverse=True)[:3]
        top_adders_text = ""
        for i, (uid, count) in enumerate(top_adders, 1):
            try:
                name = (await context.bot.get_chat_member(chat_id, uid)).user.first_name
            except:
                name = "کاربر ناشناس"
            top_adders_text += f"◂ نفر {i} {medals[i-1]} :( {count} اد | {name} )\n"
        if not top_adders_text:
            top_adders_text = "◂ اطلاعاتی یافت نشد."

        text = f"""
◄ آمار فعالیت گروه از 00:00 تا این لحظه :
• تاریخ : {jalali_date}
• ساعت : {time_str}

─┅━ پیام های امروز ━┅─
◂ کل پیام ها : {sum(data['messages'].values())}
◂ پیام فرواردی : {data['forwards']}
◂ متن : {sum([v for k,v in data['messages'].items()]) - data['forwards']}
◂ استیکر : {data['stickers']}
◂ استیکر متحرک : {data['animated_stickers']}
◂ گیف : {data['animations']}
◂ عکس : {data['photos']}
◂ ویس : {data['voices']}
◂ موزیک : {data['audios']}
◂ فیلم : {data['videos']}
◂ فیلم سلفی : {data['video_notes']}
◂ فایل : {data.get('files',0)}

─┅━ فعال ترین های امروز ━┅─
{top_today_text}

─━ بهترین عضو کننده های امروز ━─
{top_adders_text}

─┅━ ورودی و خروجی عضو ━┅─
◂ اعضای وارد شده با لینک : {data['joins_link']}
◂ اعضای اد شده : {data['joins_added']}
◂ اعضای لفت داده : {data['lefts']}
◂ اعضای اخراج شده : {data['kicked']}
◂ کل اعضای وارد شده : {data['joins_link'] + data['joins_added']}
◂ کل اعضای خارج شده : {data['lefts'] + data['kicked']}

─┅━ فعال ترین های کل ━┅─
{top_all_text}
"""
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
    for chat_id in list(stats.keys()):
        stats[chat_id] = {}
    save_stats(stats)
    print("🧹 آمار روز گذشته پاک شد ✅")
