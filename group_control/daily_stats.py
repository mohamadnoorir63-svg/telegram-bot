      # ======================= 📊 سیستم آمار پیشرفته تلگرام (کامل - با کارت گرافیکی Top5) =======================

import os
import json
import asyncio
from datetime import datetime, timedelta
import jdatetime
from telegram import Update
from telegram.ext import ContextTypes
from PIL import Image, ImageDraw, ImageFont, ImageOps
import requests
from io import BytesIO

# ------------------- تنظیمات -------------------

STATS_FILE = "advanced_stats.json"
SUDO_ID = 8588347189  # آیدی سودو شما
SAVE_INTERVAL = 300    # ذخیره هر 5 دقیقه

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

# ------------------- روز جدید -------------------

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

    if msg.forward_from or msg.forward_from_chat:
        data["forwards"] += 1
    elif msg.video: data["videos"] += 1
    elif msg.video_note: data["video_notes"] += 1
    elif msg.audio: data["audios"] += 1
    elif msg.voice: data["voices"] += 1
    elif msg.photo: data["photos"] += 1
    elif msg.animation: data["animations"] += 1
    elif msg.sticker:
        if getattr(msg.sticker, "is_animated", False):
            data["animated_stickers"] += 1
        else:
            data["stickers"] += 1

    if msg.entities:
        for entity in msg.entities:
            if entity.type == "url": data["links"] += 1
            elif entity.type == "mention": data["mentions"] += 1
            elif entity.type == "hashtag": data["hashtags"] += 1

    if msg.reply_to_message: data["replies"] += 1

    uid = str(user.id)
    data["messages"][uid] = data["messages"].get(uid, 0) + 1
    data["message_length"][uid] = data["message_length"].get(uid, 0) + len(msg.text or "")
    save_queue.add(chat_id)

# ------------------- ورود و خروج -------------------

async def record_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not getattr(update.message, "new_chat_members", None):
        return
    chat_id = str(update.effective_chat.id)
    today = datetime.now().strftime("%Y-%m-%d")
    init_daily_stats(chat_id, today)
    data = stats[chat_id][today]
    for member in update.message.new_chat_members:
        if member.is_bot: continue
        if update.message.from_user and update.message.from_user.id != member.id:
            data["joins_added"] += 1
            adder_id = str(update.message.from_user.id)
            data["joins_added_per_user"][adder_id] = data["joins_added_per_user"].get(adder_id,0)+1
        else:
            data["joins_link"] += 1
    save_queue.add(chat_id)

async def record_left_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not getattr(update.message, "left_chat_member", None):
        return
    chat_id = str(update.effective_chat.id)
    today = datetime.now().strftime("%Y-%m-%d")
    init_daily_stats(chat_id, today)
    stats[chat_id][today]["lefts"] += 1
    save_queue.add(chat_id)

# ------------------- نمایش اطلاعات کاربر با مقام -------------------
async def show_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = str(update.effective_chat.id)

    # بررسی دسترسی (سودو یا مدیر/مالک)
    if user.id != SUDO_ID:
        try:
            member = await context.bot.get_chat_member(chat_id, user.id)
            if member.status not in ["creator", "administrator"]:
                return
        except:
            return

    # هدف: ریپلای شده یا خود کاربر
    target = update.message.reply_to_message.from_user if update.message.reply_to_message else user

    jalali_date = jdatetime.datetime.now().strftime("%A %d %B %Y")
    time_str = datetime.now().strftime("%H:%M:%S")

    # مقام کاربر
    if target.id == SUDO_ID:
        role = "💎 سودو"
    else:
        try:
            member = await context.bot.get_chat_member(chat_id, target.id)
            if member.status == "creator":
                role = "👑 مالک"
            elif member.status == "administrator":
                role = "🛡️ مدیر"
            else:
                role = "👤 عضو عادی"
        except:
            role = "👤 عضو عادی"

    # تعداد پیام‌های امروز
    today = datetime.now().strftime("%Y-%m-%d")
    total_messages = 0
    if chat_id in stats and today in stats[chat_id]:
        total_messages = stats[chat_id][today]["messages"].get(str(target.id), 0)

    # تعداد اد اضافه شده امروز
    total_added = 0
    if chat_id in stats and today in stats[chat_id]:
        total_added = stats[chat_id][today]["joins_added_per_user"].get(str(target.id), 0)

    # متن پیام
    user_link = f"<a href='tg://user?id={target.id}'>{target.first_name}</a>"
    text = (
        f"🧿 <b>اطلاعات کاربر:</b>\n\n"
        f"👤 نام: {user_link}\n"
        f"💬 یوزرنیم: {getattr(target,'username','---')}\n"
        f"🆔 آیدی عددی: <code>{target.id}</code>\n"
        f"🎖 مقام: {role}\n"
        f"📊 تعداد پیام امروز: {total_messages}\n"
        f"📌 تعداد اد اضافه‌شده امروز: {total_added}\n"
        f"📆 تاریخ: {jalali_date}\n"
        f"🕒 ساعت: {time_str}\n"
        f"🆔 آیدی عددی گروه: {chat_id}"
    )

    try:
        photos = await context.bot.get_user_profile_photos(target.id, limit=1)
        if photos.total_count > 0:
            photo = photos.photos[0][-1].file_id
            msg = await context.bot.send_photo(chat_id, photo=photo, caption=text, parse_mode="HTML")
        else:
            msg = await update.message.reply_text(text, parse_mode="HTML")
    except:
        msg = await update.message.reply_text(text, parse_mode="HTML")

    # حذف پیام بعد از 15 ثانیه
    await asyncio.sleep(15)
    try:
        await context.bot.delete_message(chat_id, msg.message_id)
    except:
        pass
# ------------------- ساخت عکس Top5 (سازگار با Pillow 10+) -------------------

async def create_top5_image(context, chat_id, today):
    data = stats[chat_id][today]
    top_today = sorted(data["messages"].items(), key=lambda x:x[1], reverse=True)[:5]

    width, height = 820, 980
    bg_color = (39,41,54)
    card_color = (32,34,45)
    text_color = (230,230,230)
    img = Image.new("RGB",(width,height),bg_color)
    draw = ImageDraw.Draw(img)

    # فونت‌ها
    def _load_font(path,size):
        try: return ImageFont.truetype(path,size)
        except:
            try: return ImageFont.truetype("DejaVuSans-Bold.ttf",size)
            except: return ImageFont.load_default()

    font_title = _load_font("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",36)
    font_name = _load_font("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",28)
    font_small = _load_font("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",20)

    title_text = "لیست کسانی که بیشترین پیام را ارسال کردند"
    bbox = draw.textbbox((0,0),title_text,font=font_title)
    w_title = bbox[2]-bbox[0]
    draw.text(((width-w_title)/2,30),title_text,fill=text_color,font=font_title)

    x_card, y_card = 60, 110
    card_w, card_h = width-2*x_card, 110
    gap, rank = 20, 1

    for uid, count in top_today:
        card = Image.new("RGB",(card_w,card_h),card_color)
        card_draw = ImageDraw.Draw(card)
        card_draw.text((18,30),str(rank),fill=text_color,font=font_title)

        # آواتار
        try:
            member = await context.bot.get_chat_member(chat_id, uid)
            name = member.user.first_name
            photos = await context.bot.get_user_profile_photos(uid,limit=1)
            if photos.total_count>0:
                file = await context.bot.get_file(photos.photos[0][-1].file_id)
                resp = requests.get(file.file_path,timeout=10)
                avatar = Image.open(BytesIO(resp.content)).convert("RGBA").resize((84,84))
            else: avatar = Image.new("RGBA",(84,84),(70,70,70,255))
        except: 
            name = "کاربر ناشناس"
            avatar = Image.new("RGBA",(84,84),(70,70,70,255))

        mask = Image.new("L",avatar.size,0)
        ImageDraw.Draw(mask).ellipse((0,0,avatar.size[0],avatar.size[1]),fill=255)
        avatar = ImageOps.fit(avatar,avatar.size)
        card.paste(avatar,(70,13),mask)

        # نام و تعداد پیام
        name_display = (name[:22]+"...") if len(name)>22 else name
        card_draw.text((180,24),name_display,fill=text_color,font=font_name)
        count_text = f"{count} پیام"
        bbox_count = card_draw.textbbox((0,0),count_text,font=font_small)
        w_count = bbox_count[2]-bbox_count[0]
        card_draw.text((card_w-w_count-20,40),count_text,fill=(200,200,200),font=font_small)

        # گوشه‌های گرد
        radius = 18
        rounded = Image.new("RGBA",card.size,(0,0,0,0))
        rounded_draw = ImageDraw.Draw(rounded)
        rounded_draw.rounded_rectangle([(0,0),card.size],radius=radius,fill=card_color)
        rounded.paste(card,(0,0),card if card.mode=="RGBA" else None)

        img.paste(rounded.convert("RGB"),(x_card,y_card))
        y_card += card_h+gap
        rank += 1

    while rank<=5:
        card = Image.new("RGB",(card_w,card_h),card_color)
        card_draw = ImageDraw.Draw(card)
        card_draw.text((18,30),str(rank),fill=text_color,font=font_title)
        card_draw.text((180,24),"—",fill=(160,160,160),font=font_name)
        count_text = "0 پیام"
        bbox_count = card_draw.textbbox((0,0),count_text,font=font_small)
        w_count = bbox_count[2]-bbox_count[0]
        card_draw.text((card_w-w_count-20,40),count_text,fill=(120,120,120),font=font_small)
        rounded = Image.new("RGBA",card.size,(0,0,0,0))
        rounded_draw = ImageDraw.Draw(rounded)
        rounded_draw.rounded_rectangle([(0,0),card.size],radius=18,fill=card_color)
        rounded.paste(card,(0,0),card if card.mode=="RGBA" else None)
        img.paste(rounded.convert("RGB"),(x_card,y_card))
        y_card += card_h+gap
        rank +=1

    out_path = f"top5_{chat_id}_{today}.png"
    try: img.save(out_path)
    except Exception as e: 
        print("Error saving image:",e)
        out_path=None
    return out_path

# ------------------- نمایش آمار گروه (عکس + متن) -------------------

async def show_group_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = str(update.effective_chat.id)
    today = datetime.now().strftime("%Y-%m-%d")

    if user.id != SUDO_ID:
        try:
            member = await context.bot.get_chat_member(chat_id,user.id)
            if member.status not in ["creator","administrator"]: return
        except: return

    if chat_id not in stats or today not in stats[chat_id]:
        msg = await update.message.reply_text("ℹ️ هنوز فعالیتی برای امروز ثبت نشده است.")
        await asyncio.sleep(15)
        try: await context.bot.delete_message(chat_id,msg.message_id)
        except: pass
        return

    data = stats[chat_id][today]
    now = datetime.now()
    time_str = now.strftime("%H:%M:%S")
    jalali_date = jdatetime.datetime.now().strftime("%A %d %B %Y")

    # نفرات برتر امروز
    top_today = sorted(data["messages"].items(), key=lambda x:x[1], reverse=True)[:3]
    medals=["🥇","🥈","🥉"]
    top_today_text=""
    for i,(uid,count) in enumerate(top_today,1):
        try: name=(await context.bot.get_chat_member(chat_id,uid)).user.first_name
        except: name="کاربر ناشناس"
        top_today_text+=f"◂ نفر {i} {medals[i-1]} :( {count} پیام | {name} )\n"
    if not top_today_text: top_today_text="◂ اطلاعاتی یافت نشد."

    top_adders = sorted(data["joins_added_per_user"].items(), key=lambda x:x[1], reverse=True)[:3]
    top_adders_text=""
    for i,(uid,count) in enumerate(top_adders,1):
        try: name=(await context.bot.get_chat_member(chat_id,uid)).user.first_name
        except: name="کاربر ناشناس"
        top_adders_text+=f"◂ نفر {i} {medals[i-1]} :( {count} اد | {name} )\n"
    if not top_adders_text: top_adders_text="◂ اطلاعاتی یافت نشد."

    total_msgs_all={}
    for day_data in stats.get(chat_id,{}).values():
        for uid,count in day_data["messages"].items():
            total_msgs_all[uid]=total_msgs_all.get(uid,0)+count
    top_all = sorted(total_msgs_all.items(), key=lambda x:x[1], reverse=True)[:3]
    top_all_text=""
    for i,(uid,count) in enumerate(top_all,1):
        try: name=(await context.bot.get_chat_member(chat_id,uid)).user.first_name
        except: name="کاربر ناشناس"
        top_all_text+=f"◂ نفر {i} {medals[i-1]} :( {count} پیام | {name} )\n"
    if not top_all_text: top_all_text="◂ اطلاعاتی یافت نشد."

    stats_text = f"""
◄ آمار فعالیت گروه از 00:00 تا این لحظه : • تاریخ : {jalali_date} • ساعت : {time_str}

─┅━ پیام های امروز ━┅─ 
◂ کل پیام ها : {sum(data['messages'].values())} 
◂ پیام فرواردی : {data['forwards']} 
◂ متن : {sum([v for k,v in data['messages'].items()])-data['forwards']} 
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

─┅━ فعال ترین های کل ━┅─ 
{top_all_text}
"""

    # ساخت عکس و ارسال با متن
    img_path = await create_top5_image(context, chat_id, today)
    if img_path:
        try:
            with open(img_path,"rb") as f:
                msg = await context.bot.send_photo(
                    chat_id,
                    photo=f,
                    caption=stats_text,
                    parse_mode="HTML"
                )
            os.remove(img_path)
            await asyncio.sleep(15)
            try: await context.bot.delete_message(chat_id,msg.message_id)
            except: pass
        except Exception as e:
            print("Error sending top5 with caption:",e)      
                
# ------------------- آمار شبانه و پاکسازی -------------------
async def send_nightly_stats(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    for chat_id, days in stats.items():
        if yesterday in days:
            data = days[yesterday]
            total_msgs = sum(data["messages"].values())
            report = (
                f"🌙 آمار شب گذشته ({yesterday})\n"
                f"📩 کل پیام‌ها: {total_msgs}\n"
                f"👥 اعضا اضافه‌شده: {data['joins_added']}\n"
                f"🚪 اعضا خارج‌شده: {data['lefts']}"
            )
            try:
                await context.bot.send_message(chat_id, report, parse_mode="HTML")
            except Exception as e:
                print(f"Error sending nightly stats to {chat_id}: {e}")

    # پاکسازی آمار روز گذشته
    for chat_id in list(stats.keys()):
        stats[chat_id] = {}
    save_stats(stats)
    print("🧹 آمار روز گذشته پاک شد ✅")
