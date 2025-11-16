# ======================= 📊 سیستم آمار پیشرفته تلگرام (نسخه گرافیکی ۵ نفر برتر) =======================

import os
import json
import asyncio
from datetime import datetime, timedelta
import jdatetime
from telegram import Update
from telegram.ext import ContextTypes
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

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

# ------------------- ثبت پیام -------------------

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

    # پیام
    uid = str(user.id)
    data["messages"][uid] = data["messages"].get(uid, 0) + 1
    data["message_length"][uid] = data["message_length"].get(uid, 0) + len(msg.text or "")
    save_queue.add(chat_id)

# ------------------- تصویر ۵ نفر برتر -------------------

async def create_top5_image(context, chat_id, today):
    data = stats[chat_id][today]
    top_today = sorted(data["messages"].items(), key=lambda x: x[1], reverse=True)[:5]

    # ابعاد تصویر
    img = Image.new("RGB", (700, 800), "#2B2D42")
    draw = ImageDraw.Draw(img)

    # فونت‌ها (ممکن است نیاز به تغییر مسیر داشته باشند)
    try:
        font_bold = ImageFont.truetype("arialbd.ttf", 36)
        font_small = ImageFont.truetype("arial.ttf", 28)
    except:
        font_bold = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # عنوان بالای تصویر
    draw.text((150, 40), "لیست کسانی که بیشترین پیام را ارسال کردند", fill="white", font=font_small)

    y = 120
    rank = 1
    for uid, count in top_today:
        try:
            member = await context.bot.get_chat_member(chat_id, uid)
            name = member.user.first_name
            photos = await context.bot.get_user_profile_photos(uid, limit=1)
            if photos.total_count > 0:
                file = await context.bot.get_file(photos.photos[0][-1].file_id)
                resp = requests.get(file.file_path)
                avatar = Image.open(BytesIO(resp.content)).resize((80, 80))
            else:
                avatar = Image.new("RGB", (80, 80), "#444")
        except:
            name = "کاربر ناشناس"
            avatar = Image.new("RGB", (80, 80), "#444")

        # کارت کاربر
        card = Image.new("RGB", (600, 100), "#1E1F2A")
        draw_card = ImageDraw.Draw(card)

        # شماره رتبه
        draw_card.text((20, 35), f"{rank}", fill="white", font=font_bold)

        # آواتار
        mask = Image.new("L", (80, 80), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, 80, 80), fill=255)
        avatar.putalpha(mask)
        card.paste(avatar, (80, 10), avatar)

        # نام و تعداد پیام
        draw_card.text((180, 25), f"{name[:18]}", fill="white", font=font_small)
        draw_card.text((500, 40), f"{count} پیام", fill="#CCCCCC", font=font_small)

        img.paste(card, (50, y))
        y += 120
        rank += 1

    output_path = f"top5_{chat_id}.png"
    img.save(output_path)
    return output_path

# ------------------- نمایش آمار گروه -------------------

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

    # ساخت تصویر ۵ نفر برتر
    img_path = await create_top5_image(context, chat_id, today)
    await context.bot.send_photo(chat_id, photo=open(img_path, "rb"))

    # بقیه متن آمار معمولی (اختیاری)
    data = stats[chat_id][today]
    total_msgs = sum(data["messages"].values())
    jalali_date = jdatetime.datetime.now().strftime("%A %d %B %Y")
    text = f"📊 آمار امروز ({jalali_date})\n📩 مجموع پیام‌ها: {total_msgs}"
    msg = await update.message.reply_text(text, parse_mode="HTML")
    await asyncio.sleep(15)
    await context.bot.delete_message(chat_id, msg.message_id)
    os.remove(img_path)
