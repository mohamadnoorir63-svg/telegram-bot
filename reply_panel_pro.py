# ========================= ✳️ Reply Panel Pro =========================
# نسخه حرفه‌ای هماهنگ با Khenqol Cloud+ Supreme Pro 8.5.1
# پشتیبانی از: متن، عکس، ویدیو، موزیک، استیکر، ویدیو‌نوت، ویس
# طراحی شده برای سیستم ذخیره پاسخ‌های پیشرفته با پنل انتخاب و حالت تصادفی

import os
import json
import random
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

REPLY_FILE = "memory.json"

# ---------------------- 📂 توابع پایه ----------------------
def load_replies():
    """بارگذاری پاسخ‌ها از فایل حافظه"""
    if not os.path.exists(REPLY_FILE):
        return {"replies": {}}
    with open(REPLY_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            if "replies" not in data:
                data["replies"] = {}
            return data
        except:
            return {"replies": {}}

def save_replies(data):
    """ذخیره پاسخ‌ها در حافظه"""
    with open(REPLY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------------------- 🎯 افزودن پاسخ ----------------------
async def add_reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع ساخت پاسخ جدید با پنل تنظیمات"""
    message = update.message
    text = message.text.replace("افزودن پاسخ", "").strip()
    if not text:
        return await message.reply_text("❗ لطفاً بعد از دستور بنویس: افزودن پاسخ <نام>")

    # ذخیره وضعیت در حافظه موقت کاربر
    context.user_data["reply_key"] = text
    context.user_data["reply_data"] = {
        "media": [],
        "text": [],
        "access": "همه",
        "send_mode": "همه",
        "random_mode": False,
    }

    # ساخت پنل تنظیمات
    keyboard = [
        [
            InlineKeyboardButton("👥 همه ✅", callback_data="access_all"),
            InlineKeyboardButton("👑 ادمین", callback_data="access_admin")
        ],
        [
            InlineKeyboardButton("📢 گروه", callback_data="send_group"),
            InlineKeyboardButton("👤 شخصی", callback_data="send_private")
        ],
        [
            InlineKeyboardButton("🎲 تصادفی", callback_data="random_toggle"),
            InlineKeyboardButton("💾 ذخیره", callback_data="save_reply")
        ],
        [InlineKeyboardButton("🗑 حذف", callback_data="delete_reply")]
    ]

    await message.reply_text(
        f"🧠 در حال ساخت پاسخ جدید برای: <b>{text}</b>\n\n"
        "📌 روی پیامی (متنی یا رسانه‌ای) ریپلای کن تا ذخیره شود.\n"
        "وقتی تموم شد از دکمه‌های پایین تنظیمات را انتخاب کن و روی 💾 ذخیره بزن.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------------- 📨 دریافت انواع فایل ----------------------
async def message_collector(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت هر نوع پیام و ذخیره موقت آن در حافظه کاربر"""
    if "reply_key" not in context.user_data:
        return  # در حالت افزودن نیست

    data = context.user_data["reply_data"]
    msg = update.message

    # 📄 متن
    if msg.text:
        data["text"].append(msg.text.strip())

    # 🖼 عکس
    elif msg.photo:
        file_id = msg.photo[-1].file_id
        data["media"].append(("photo", file_id))

    # 🎬 ویدیو
    elif msg.video:
        data["media"].append(("video", msg.video.file_id))

    # 🎵 موزیک
    elif msg.audio:
        data["media"].append(("audio", msg.audio.file_id))

    # 🎙 ویس
    elif msg.voice:
        data["media"].append(("voice", msg.voice.file_id))

    # 📹 ویدیو‌نوت
    elif msg.video_note:
        data["media"].append(("video_note", msg.video_note.file_id))

    # 💬 استیکر
    elif msg.sticker:
        data["media"].append(("sticker", msg.sticker.file_id))

    await msg.reply_text("✅ پیام موقتاً ذخیره شد. بعد از اتمام، دکمه 💾 ذخیره را بزن.")

# ---------------------- 🧮 مدیریت پنل ----------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت کلیک روی دکمه‌های پنل"""
    query = update.callback_query
    await query.answer()

    if "reply_key" not in context.user_data:
        return await query.edit_message_text("❌ حالت فعال نیست یا منقضی شده!")

    key = context.user_data["reply_key"]
    reply_data = context.user_data["reply_data"]
    data = load_replies()
    replies = data.get("replies", {})

    # ⚙️ تغییر تنظیمات
    if query.data == "access_all":
        reply_data["access"] = "همه"
    elif query.data == "access_admin":
        reply_data["access"] = "ادمین"
    elif query.data == "send_group":
        reply_data["send_mode"] = "گروه"
    elif query.data == "send_private":
        reply_data["send_mode"] = "شخصی"
    elif query.data == "random_toggle":
        reply_data["random_mode"] = not reply_data["random_mode"]

    # 💾 ذخیره
    elif query.data == "save_reply":
        if key not in replies:
            replies[key] = []

        entry = {
            "text": reply_data["text"],
            "media": reply_data["media"],
            "access": reply_data["access"],
            "send_mode": reply_data["send_mode"],
            "random": reply_data["random_mode"],
        }

        replies[key].append(entry)
        save_replies(data)
        context.user_data.clear()
        return await query.edit_message_text(
            f"✅ پاسخ برای '{key}' با موفقیت ذخیره شد و پنل بسته شد."
        )

    # 🗑 حذف پاسخ
    elif query.data == "delete_reply":
        if key in replies:
            del replies[key]
            save_replies(data)
            context.user_data.clear()
            return await query.edit_message_text(f"🗑 پاسخ '{key}' حذف شد و پنل بسته شد.")
        else:
            return await query.edit_message_text("⚠️ پاسخی برای حذف وجود ندارد.")

    # 🔄 به‌روزرسانی وضعیت دکمه‌ها
    random_state = "✅" if reply_data["random_mode"] else ""
    keyboard = [
        [
            InlineKeyboardButton(
                "👥 همه ✅" if reply_data["access"] == "همه" else "👥 همه",
                callback_data="access_all"
            ),
            InlineKeyboardButton(
                "👑 ادمین ✅" if reply_data["access"] == "ادمین" else "👑 ادمین",
                callback_data="access_admin"
            )
        ],
        [
            InlineKeyboardButton(
                "📢 گروه ✅" if reply_data["send_mode"] == "گروه" else "📢 گروه",
                callback_data="send_group"
            ),
            InlineKeyboardButton(
                "👤 شخصی ✅" if reply_data["send_mode"] == "شخصی" else "👤 شخصی",
                callback_data="send_private"
            )
        ],
        [
            InlineKeyboardButton(f"🎲 تصادفی {random_state}", callback_data="random_toggle"),
            InlineKeyboardButton("💾 ذخیره", callback_data="save_reply")
        ],
        [InlineKeyboardButton("🗑 حذف", callback_data="delete_reply")]
    ]
    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))

# ---------------------- 💬 پاسخ خودکار ----------------------
async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال پاسخ هنگام دریافت کلید ذخیره‌شده (پشتیبانی از متن و رسانه)"""
    msg = update.message
    if not msg or not msg.text:
        return

    text = msg.text.strip()
    all_data = load_replies()
    replies = all_data.get("replies", {})

    if text not in replies:
        return

    options = replies[text]
    if not options:
        return

    # 🎲 انتخاب پاسخ (تصادفی یا معمولی)
    selected = random.choice(options)
    if selected.get("random"):
        reply_text = random.choice(selected.get("text", []) or [""])
        media_list = selected.get("media", [])
        media = random.choice(media_list) if media_list else None
    else:
        reply_text = "\n".join(selected.get("text", []) or [])
        media = selected.get("media", [None])[0]

    # 🚀 ارسال پیام
    try:
        if media:
            mtype, fid = media
            if mtype == "photo":
                await msg.reply_photo(fid, caption=reply_text or None)
            elif mtype == "video":
                await msg.reply_video(fid, caption=reply_text or None)
            elif mtype == "audio":
                await msg.reply_audio(fid, caption=reply_text or None)
            elif mtype == "voice":
                await msg.reply_voice(fid, caption=reply_text or None)
            elif mtype == "video_note":
                await msg.reply_video_note(fid)
            elif mtype == "sticker":
                await msg.reply_sticker(fid)
            else:
                await msg.reply_text(reply_text or "⚠️ نوع رسانه پشتیبانی نمی‌شود.")
        elif reply_text:
            await msg.reply_text(reply_text)
    except Exception as e:
        await msg.reply_text(f"⚠️ خطا در ارسال پاسخ: {e}")
