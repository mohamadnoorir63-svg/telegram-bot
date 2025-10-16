# ========================= ✳️ Reply Panel Pro++ 8.5.3 =========================
# نسخه جدید با قابلیت ویرایش، حذف، مشاهده و افزودن پاسخ‌ها
# طراحی‌شده برای ربات خنگول Cloud+ Supreme Pro Stable+
# ------------------------------------------------------------

import os
import json
import random
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

REPLY_FILE = "memory.json"

# ---------------------- 📂 توابع فایل ----------------------
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
    """ذخیره پاسخ‌ها در فایل حافظه"""
    with open(REPLY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------------------- 🎯 افزودن پاسخ ----------------------
async def add_reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """افزودن پاسخ جدید"""
    message = update.message
    text = message.text.replace("افزودن پاسخ", "").strip()
    if not text:
        return await message.reply_text("❗ بنویس: افزودن پاسخ <کلمه>")

    context.user_data["reply_mode"] = "add"
    context.user_data["reply_key"] = text
    context.user_data["reply_data"] = {"text": [], "media": []}

    keyboard = [
        [InlineKeyboardButton("💾 ذخیره", callback_data="save_reply")],
        [InlineKeyboardButton("❌ انصراف", callback_data="cancel_reply")]
    ]

    await message.reply_text(
        f"🧠 در حال افزودن پاسخ برای: <b>{text}</b>\n"
        "پیام‌هات (متن یا عکس و...) رو بفرست.\n"
        "وقتی تموم شد روی 💾 ذخیره بزن.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------------- ✏️ ویرایش پاسخ ----------------------
async def start_edit_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فعال‌سازی حالت ویرایش برای پاسخ انتخاب‌شده"""
    query = update.callback_query
    key = query.data.replace("edit_", "")

    context.user_data["reply_mode"] = "edit"
    context.user_data["reply_key"] = key
    context.user_data["reply_data"] = {"text": [], "media": []}

    keyboard = [
        [InlineKeyboardButton("💾 ذخیره تغییرات", callback_data="save_reply_edit")],
        [InlineKeyboardButton("❌ انصراف", callback_data="cancel_reply")]
    ]

    await query.edit_message_text(
        f"✏️ در حال ویرایش پاسخ <b>{key}</b>\n"
        "پیام جدیدت (متن یا مدیا) رو بفرست.\n"
        "وقتی تموم شد روی 💾 ذخیره تغییرات بزن.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------------- 📨 جمع‌آوری پیام ----------------------
async def message_collector(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ذخیره موقت پیام‌های کاربر"""
    if "reply_key" not in context.user_data:
        return

    msg = update.message
    data = context.user_data["reply_data"]

    if msg.text:
        data["text"].append(msg.text.strip())
    elif msg.photo:
        data["media"].append(("photo", msg.photo[-1].file_id))
    elif msg.video:
        data["media"].append(("video", msg.video.file_id))
    elif msg.audio:
        data["media"].append(("audio", msg.audio.file_id))
    elif msg.voice:
        data["media"].append(("voice", msg.voice.file_id))
    elif msg.video_note:
        data["media"].append(("video_note", msg.video_note.file_id))
    elif msg.sticker:
        data["media"].append(("sticker", msg.sticker.file_id))

    await msg.reply_text("✅ پیام ذخیره شد. بعد از اتمام روی 💾 بزن.")

# ---------------------- 🧮 دکمه‌ها ----------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_replies()
    replies = data.get("replies", {})

    # انصراف
    if query.data == "cancel_reply":
        context.user_data.clear()
        return await query.edit_message_text("❌ عملیات لغو شد.")

    # ذخیره پاسخ جدید
    if query.data == "save_reply":
        if "reply_key" not in context.user_data:
            return await query.edit_message_text("⛔ حالت افزودن فعال نیست!")

        key = context.user_data["reply_key"]
        reply_data = context.user_data["reply_data"]
        if key not in replies:
            replies[key] = []
        replies[key].append(reply_data)
        data["replies"] = replies
        save_replies(data)
        context.user_data.clear()

        return await query.edit_message_text(f"✅ پاسخ '{key}' ذخیره شد!")

    # ذخیره ویرایش
    if query.data == "save_reply_edit":
        key = context.user_data.get("reply_key")
        reply_data = context.user_data["reply_data"]

        if not key or key not in replies:
            return await query.edit_message_text("⚠️ پاسخ مورد نظر یافت نشد.")

        # جایگزین محتوای قبلی با جدید
        replies[key] = [reply_data]
        data["replies"] = replies
        save_replies(data)
        context.user_data.clear()
        return await query.edit_message_text(f"✅ پاسخ '{key}' ویرایش شد!")

    # حذف
    if query.data.startswith("delete_"):
        key = query.data.replace("delete_", "")
        if key in replies:
            del replies[key]
            save_replies(data)
            await query.edit_message_text(f"🗑 پاسخ '{key}' حذف شد.")
        else:
            await query.edit_message_text("⚠️ پاسخی با این نام وجود ندارد.")

    # پیش‌نمایش
    if query.data.startswith("preview_"):
        key = query.data.replace("preview_", "")
        if key not in replies:
            return await query.edit_message_text("⚠️ پاسخی یافت نشد.")
        reply = replies[key][-1]
        txt = "\n".join(reply.get("text", [])) or "—"
        await query.message.reply_text(f"📋 پیش‌نمایش پاسخ '{key}':\n\n{txt}")

# ---------------------- 🧭 مدیریت پاسخ‌ها ----------------------
async def manage_replies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست تمام پاسخ‌ها با دکمه ویرایش"""
    data = load_replies()
    replies = data.get("replies", {})

    if not replies:
        return await update.message.reply_text("ℹ️ هنوز هیچ پاسخی ثبت نشده!")

    keyboard = []
    for key in replies.keys():
        keyboard.append([
            InlineKeyboardButton(f"📋 {key}", callback_data=f"preview_{key}"),
            InlineKeyboardButton("✏️ ویرایش", callback_data=f"edit_{key}"),
            InlineKeyboardButton("❌ حذف", callback_data=f"delete_{key}")
        ])

    await update.message.reply_text(
        "🧩 لیست پاسخ‌های ذخیره‌شده:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------------- 💬 پاسخ خودکار ----------------------
async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال پاسخ هنگام دریافت کلید ذخیره‌شده"""
    msg = update.message
    if not msg or not msg.text:
        return

    text = msg.text.strip()
    data = load_replies()
    replies = data.get("replies", {})

    if text not in replies:
        return

    entry = random.choice(replies[text])
    reply_text = "\n".join(entry.get("text", [])) if entry.get("text") else ""
    media = entry.get("media", [])

    try:
        if media:
            mtype, fid = random.choice(media)
            if mtype == "photo":
                await msg.reply_photo(fid, caption=reply_text or None)
            elif mtype == "video":
                await msg.reply_video(fid, caption=reply_text or None)
            elif mtype == "audio":
                await msg.reply_audio(fid, caption=reply_text or None)
            elif mtype == "voice":
                await msg.reply_voice(fid, caption=reply_text or None)
            elif mtype == "sticker":
                await msg.reply_sticker(fid)
            elif mtype == "video_note":
                await msg.reply_video_note(fid)
        elif reply_text:
            await msg.reply_text(reply_text)
    except Exception as e:
        await msg.reply_text(f"⚠️ خطا در ارسال پاسخ: {e}")
