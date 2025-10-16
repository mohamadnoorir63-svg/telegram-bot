# ========================= ✳️ Reply Panel Pro =========================
# نسخه حرفه‌ای هماهنگ با Khenqol Cloud+ Supreme Pro 8.5.1
# پشتیبانی از: متن، عکس، ویدیو، موزیک، استیکر، ویدیو‌نوت، ویس
# طراحی شده برای سیستم ذخیره پاسخ‌های پیشرفته با پنل انتخاب

import os
import json
import random
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from telegram.ext import ContextTypes

REPLY_FILE = "memory.json"

# ---------------------- 📂 توابع پایه ----------------------
def load_replies():
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
    with open(REPLY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------------------- 🎯 افزودن پاسخ ----------------------
async def add_reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع ساخت پاسخ جدید با پنل انتخاب"""
    message = update.message
    text = message.text.replace("افزودن پاسخ", "").strip()
    if not text:
        return await message.reply_text("❗ لطفاً بعد از دستور بنویس: افزودن پاسخ <نام>")

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
        [InlineKeyboardButton("👥 همه ✅", callback_data="access_all"),
         InlineKeyboardButton("👑 ادمین", callback_data="access_admin")],
        [InlineKeyboardButton("📢 گروه", callback_data="send_group"),
         InlineKeyboardButton("👤 شخصی", callback_data="send_private")],
        [InlineKeyboardButton("🎲 تصادفی", callback_data="random_toggle"),
         InlineKeyboardButton("💾 ذخیره", callback_data="save_reply")],
        [InlineKeyboardButton("🗑 حذف", callback_data="delete_reply")]
    ]
    await message.reply_text(
        f"🧠 در حال ساخت پاسخ جدید برای: <b>{text}</b>\n\n"
        "📌 روی پیامی (متنی یا رسانه‌ای) ریپلای کن تا ذخیره شود.\n"
        "سپس با دکمه‌ها تنظیمات را انتخاب کن و ذخیره بزن.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------------- 📨 دریافت فایل‌ها ----------------------
async def message_collector(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت هر نوع پیام برای ذخیره موقت"""
    if "reply_key" not in context.user_data:
        return  # در حالت افزودن نیست

    data = context.user_data["reply_data"]
    msg = update.message

    # ذخیره متن
    if msg.text:
        data["text"].append(msg.text.strip())

    # ذخیره عکس
    elif msg.photo:
        photo = msg.photo[-1].file_id
        data["media"].append(("photo", photo))

    # ذخیره ویدیو
    elif msg.video:
        data["media"].append(("video", msg.video.file_id))

    # ذخیره موزیک
    elif msg.audio:
        data["media"].append(("audio", msg.audio.file_id))

    # ذخیره ویس
    elif msg.voice:
        data["media"].append(("voice", msg.voice.file_id))

    # ذخیره ویدیو‌نوت
    elif msg.video_note:
        data["media"].append(("video_note", msg.video_note.file_id))

    # ذخیره استیکر
    elif msg.sticker:
        data["media"].append(("sticker", msg.sticker.file_id))

    await msg.reply_text("✅ پیام موقتاً ذخیره شد. بعد از اتمام، دکمه 💾 ذخیره را بزن.")

# ---------------------- 🧮 کنترل پنل ----------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت دکمه‌های انتخاب پنل"""
    query = update.callback_query
    await query.answer()

    if "reply_key" not in context.user_data:
        return await query.edit_message_text("❌ حالت فعال نیست یا منقضی شده!")

    key = context.user_data["reply_key"]
    reply_data = context.user_data["reply_data"]
    data = load_replies()
    replies = data.get("replies", {})

    # تغییرات تنظیمات
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

    # ذخیره
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

    # حذف
    elif query.data == "delete_reply":
        if key in replies:
            del replies[key]
            save_replies(data)
            context.user_data.clear()
            return await query.edit_message_text(f"🗑 پاسخ '{key}' حذف شد و پنل بسته شد.")
        else:
            return await query.edit_message_text("⚠️ پاسخی برای حذف وجود ندارد.")

    # بازسازی پنل با وضعیت جدید
    random_state = "✅" if reply_data["random_mode"] else ""
    keyboard = [
        [InlineKeyboardButton("👥 همه ✅" if reply_data["access"] == "همه" else "👥 همه", callback_data="access_all"),
         InlineKeyboardButton("👑 ادمین ✅" if reply_data["access"] == "ادمین" else "👑 ادمین", callback_data="access_admin")],
        [InlineKeyboardButton("📢 گروه ✅" if reply_data["send_mode"] == "گروه" else "📢 گروه", callback_data="send_group"),
         InlineKeyboardButton("👤 شخصی ✅" if reply_data["send_mode"] == "شخصی" else "👤 شخصی", callback_data="send_private")],
        [InlineKeyboardButton(f"🎲 تصادفی {random_state}", callback_data="random_toggle"),
         InlineKeyboardButton("💾 ذخیره", callback_data="save_reply")],
        [InlineKeyboardButton("🗑 حذف", callback_data="delete_reply")]
    ]
    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))

# ---------------------- 💬 پاسخ خودکار ----------------------
async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال پاسخ هنگام دریافت کلید ذخیره‌شده"""
    text = update.message.text.strip()
    data = load_replies().get("replies", {})

    if text not in data:
        return

    replies = data[text]
    if not replies:
        return

    # انتخاب پاسخ تصادفی
    selected = random.choice(replies)
    if selected.get("random"):
        # اگر چند پاسخ دارد، یکی از آن‌ها را انتخاب کن
        if selected["text"]:
            reply_text = random.choice(selected["text"])
        else:
            reply_text = ""
        media_list = selected.get("media", [])
        if media_list:
            media = random.choice(media_list)
        else:
            media = None
    else:
        # اولین پاسخ کامل را بفرست
        reply_text = "\n".join(selected.get("text", []))
        media = selected["media"][0] if selected["media"] else None

    # ارسال
    if media:
        t, fid = media
        try:
            if t == "photo":
                await update.message.reply_photo(fid, caption=reply_text or None)
            elif t == "video":
                await update.message.reply_video(fid, caption=reply_text or None)
            elif t == "audio":
                await update.message.reply_audio(fid, caption=reply_text or None)
            elif t == "voice":
                await update.message.reply_voice(fid, caption=reply_text or None)
            elif t == "video_note":
                await update.message.reply_video_note(fid)
            elif t == "sticker":
                await update.message.reply_sticker(fid)
        except Exception as e:
            await update.message.reply_text(f"⚠️ خطا در ارسال رسانه: {e}")
    elif reply_text:
        await update.message.reply_text(reply_text)
