# ======================= 📊 سیستم آمار پیشرفته تلگرام + گرافیک =======================

import os
import json
import asyncio
from datetime import datetime, timedelta
import jdatetime
from telegram import Update
from telegram.ext import ContextTypes
from PIL import Image, ImageDraw, ImageFont
import io

# ------------------- تنظیمات -------------------

STATS_FILE = "advanced_stats.json"
VOICE_FILE = "voice_stats.json"
SUDO_ID = 8588347189
SAVE_INTERVAL = 300
FONT_PATH = "arial.ttf"  # مسیر فونت برای تصویر گرافیکی

# ------------------- بارگذاری و ذخیره -------------------

def load_json(file):
    if os.path.exists(file):
        try:
            with open(file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ خطا در خواندن {file}: {e}")
    return {}

def save_json(file, data):
    try:
        with open(file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ خطا در ذخیره {file}: {e}")

stats = load_json(STATS_FILE)
voice_data = load_json(VOICE_FILE)
save_queue = set()

async def periodic_save():
    while True:
        await asyncio.sleep(SAVE_INTERVAL)
        if save_queue:
            save_json(STATS_FILE, stats)
            save_json(VOICE_FILE, voice_data)
            save_queue.clear()
            print("💾 آمار ذخیره شد (save_queue)")

# ------------------- ایجاد روز جدید -------------------

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
            "message_length": {},
            "joins_link": 0,
            "joins_added": 0,
            "lefts": 0,
            "kicked": 0,
            "muted": 0,
            "joins_added_per_user": {}
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

    uid = str(user.id)
    data["messages"][uid] = data["messages"].get(uid, 0) + 1
    data["message_length"][uid] = data["message_length"].get(uid, 0) + len(msg.text or "")

    save_queue.add(chat_id)

# ------------------- ثبت ورود و خروج اعضا -------------------

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

async def record_left_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.left_chat_member:
        return
    chat_id = str(update.effective_chat.id)
    today = datetime.now().strftime("%Y-%m-%d")
    init_daily_stats(chat_id, today)
    stats[chat_id][today]["lefts"] += 1
    save_queue.add(chat_id)

# ------------------- نمایش آیدی کاربران -------------------

async def show_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = str(update.effective_chat.id)

    if user.id != SUDO_ID:
        try:
            member = await context.bot.get_chat_member(chat_id, user.id)
            if member.status not in ["creator", "administrator"]:
                return
        except:
            return

    target = update.message.reply_to_message.from_user if update.message.reply_to_message else user
    jalali_date = jdatetime.datetime.now().strftime("%A %d %B %Y")
    time_str = datetime.now().strftime("%H:%M:%S")

    # ویسکال
    user_voice = voice_data.get(str(target.id), {})
    total_seconds = user_voice.get("total_seconds", 0)
    voice_time = f"{total_seconds//3600:02}:{(total_seconds%3600)//60:02}" if total_seconds else "00:00"
    voice_percent = f"{user_voice.get('percent','0%')}"
    voice_rank = f"{user_voice.get('rank','---')}"

    user_link = f"<a href='tg://user?id={target.id}'>{target.first_name}</a>"

    text = (
        f"🧿 <b>اطلاعات کاربر:</b>\n\n"
        f"👤 نام: {user_link}\n"
        f"💬 یوزرنیم: {getattr(target, 'username', '---')}\n"
        f"🆔 آیدی عددی: <code>{target.id}</code>\n"
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
            msg = await context.bot.send_photo(
                chat_id, photo=photo, caption=text, parse_mode="HTML"
            )
        else:
            msg = await update.message.reply_text(text, parse_mode="HTML")
    except Exception:
        msg = await update.message.reply_text(text, parse_mode="HTML")

    await asyncio.sleep(15)
    await context.bot.delete_message(chat_id, msg.message_id)

# ------------------- ایجاد تصویر گرافیکی نفر اول -------------------

def create_leader_image(user_photo_bytes, top_text: str):
    base = Image.new("RGB", (600, 400), (30, 30, 30))
    draw = ImageDraw.Draw(base)

    font_title = ImageFont.truetype(FONT_PATH, 30)
    font_text = ImageFont.truetype(FONT_PATH, 20)

    try:
        avatar = Image.open(io.BytesIO(user_photo_bytes)).convert("RGBA").resize((150,150))
        base.paste(avatar, (225, 20))
    except:
        pass

    draw.text((50, 200), top_text, fill="white", font=font_text)
    return base

# ------------------- نمایش آمار گروه با عکس گرافیکی نفر اول -------------------

async def show_group_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = str(update.effective_chat.id)
    today = datetime.now().strftime("%Y-%m-%d")

    if user.id != SUDO_ID:
        try:
            member = await context.bot.get_chat_member(chat_id, user.id)
            if member.status not in ["creator", "administrator"]:
                return
        except:
            return

    if chat_id not in stats or today not in stats[chat_id]:
        msg = await update.message.reply_text("ℹ️ هنوز فعالیتی برای امروز ثبت نشده است.")
        await asyncio.sleep(15)
        await context.bot.delete_message(chat_id, msg.message_id)
        return

    data = stats[chat_id][today]
    top_today = sorted(data["messages"].items(), key=lambda x: x[1], reverse=True)[:3]
    medals = ["🥇", "🥈", "🥉"]

    top_first_photo_bytes = None
    top_text = ""
    for i, (uid, count) in enumerate(top_today, 1):
        try:
            member = await context.bot.get_chat_member(chat_id, uid)
            name = member.user.first_name
        except:
            name = "کاربر ناشناس"

        user_voice = voice_data.get(str(uid), {})
        total_seconds = user_voice.get("total_seconds", 0)
        voice_time = f"{total_seconds//3600:02}:{(total_seconds%3600)//60:02}" if total_seconds else "00:00"
        voice_percent = f"{user_voice.get('percent','0%')}"
        voice_rank = f"{user_voice.get('rank','---')}"

        top_text += f"◂ نفر {i} {medals[i-1]} : {count} پیام | {name}\n"
        top_text += f"   ▸ ویسکال: {voice_time} | {voice_percent} | {voice_rank}\n"

        if i == 1:
            photos = await context.bot.get_user_profile_photos(uid, limit=1)
            if photos.total_count > 0:
                file_id = photos.photos[0][-1].file_id
                file = await context.bot.get_file(file_id)
                top_first_photo_bytes = await file.download_as_bytearray()

    if top_first_photo_bytes:
        img = create_leader_image(top_first_photo_bytes, top_text)
        bio = io.BytesIO()
        bio.name = "leader.png"
        img.save(bio, "PNG")
        bio.seek(0)
        await context.bot.send_photo(chat_id, bio)
    else:
        await update.message.reply_text(top_text)

# ------------------- آمار شبانه و پاکسازی -------------------

async def send_nightly_stats(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    for chat_id, days in stats.items():
        if yesterday in days:
            data = days[yesterday]
            total_msgs = sum(data["messages"].values())
            report = (
                f"🌙 **آمار شب گذشته ({yesterday})**\n"
                f"📩 **کل پیام‌ها:** {total_msgs}\n"
                f"👥 **اعضا اضافه‌شده:** {data['joins_added']}\n"
                f"🚪 **اعضا خارج‌شده:** {data['lefts']}"
            )
            try:
                await context.bot.send_message(chat_id, report, parse_mode="HTML")
            except:
                pass
    for chat_id in list(stats.keys()):
        stats[chat_id] = {}
    save_json(STATS_FILE, stats)
    print("🧹 آمار روز گذشته پاک شد ✅")
