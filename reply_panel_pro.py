# ========================= ✳️ Reply Panel Pro++ 8.5.6 =========================
# نسخه اختصاصی برای ADMIN — دارای دکمه‌های افزودن، حذف، ویرایش، مشاهده و ذخیره
# هماهنگ با memory.json و سیستم اصلی خنگول Cloud+ Supreme Pro Stable+
# -----------------------------------------------------------------------------

import os
import json
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# مسیر فایل حافظه اصلی
REPLY_FILE = "memory.json"

# 🔹 شناسه مدیر اصلی
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# ---------------------- 📦 توابع فایل ----------------------
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

# ---------------------- 🎛 پنل مدیریت ----------------------
async def manage_replies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پنل مدیریت پاسخ‌ها فقط برای ADMIN"""
    user = update.effective_user
    if user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه از این پنل استفاده کنه!")

    data = load_replies()
    replies = data.get("replies", {})

    keyboard = [
        [InlineKeyboardButton("➕ افزودن پاسخ جدید", callback_data="add_new")],
        [InlineKeyboardButton("📋 مشاهده پاسخ‌ها", callback_data="list_replies")],
    ]

    if replies:
        keyboard.append([InlineKeyboardButton("🗑 حذف همه پاسخ‌ها", callback_data="delete_all")])

    await update.message.reply_text(
        "🧠 <b>پنل مدیریت پاسخ‌ها</b>\n"
        "از دکمه‌های زیر برای کنترل پاسخ‌ها استفاده کن 👇",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------------- 🧮 کنترل دکمه‌ها ----------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    await query.answer()

    if user.id != ADMIN_ID:
        return await query.edit_message_text("⛔ فقط مدیر اصلی اجازه‌ی استفاده از این بخش را دارد!")

    data = load_replies()
    replies = data.get("replies", {})

    # ➕ افزودن پاسخ
    if query.data == "add_new":
        context.user_data["reply_mode"] = "add_key"
        await query.edit_message_text(
            "🆕 بنویس نام کلید (کلمه‌ای که باید کاربر بگه تا پاسخ ارسال شه):"
        )
        return

    # 📋 مشاهده لیست
    if query.data == "list_replies":
        if not replies:
            return await query.edit_message_text("ℹ️ هنوز هیچ پاسخی ثبت نشده.")
        keyboard = []
        for key in replies.keys():
            keyboard.append([
                InlineKeyboardButton(f"📄 {key}", callback_data=f"open_{key}")
            ])
        await query.edit_message_text(
            "📋 لیست کلیدهای پاسخ‌ها:\nیکی رو انتخاب کن 👇",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # 🔹 باز کردن پاسخ خاص
    if query.data.startswith("open_"):
        key = query.data.replace("open_", "")
        if key not in replies:
            return await query.edit_message_text("⚠️ کلید یافت نشد!")

        entry_list = replies[key]
        text_preview = ""
        for i, r in enumerate(entry_list, 1):
            texts = "\n".join(r.get("text", [])) or "— بدون متن —"
            text_preview += f"🧩 <b>پاسخ {i}</b>:\n{texts}\n\n"

        keyboard = [
            [InlineKeyboardButton("➕ افزودن پاسخ جدید به این کلید", callback_data=f"add_{key}")],
            [InlineKeyboardButton("✏️ ویرایش پاسخ‌ها", callback_data=f"edit_{key}")],
            [InlineKeyboardButton("🗑 حذف کلید", callback_data=f"delkey_{key}")],
            [InlineKeyboardButton("⬅️ بازگشت", callback_data="list_replies")]
        ]
        await query.edit_message_text(
            f"📘 <b>{key}</b>\n\n{text_preview or '— بدون پاسخ —'}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # 🗑 حذف کلید کامل
    if query.data.startswith("delkey_"):
        key = query.data.replace("delkey_", "")
        if key in replies:
            del replies[key]
            save_replies(data)
            return await query.edit_message_text(f"🗑 تمام پاسخ‌های '{key}' حذف شدند.")
        return await query.edit_message_text("⚠️ کلید یافت نشد!")

    # 🗑 حذف همه پاسخ‌ها
    if query.data == "delete_all":
        data["replies"] = {}
        save_replies(data)
        await query.edit_message_text("🧹 تمام پاسخ‌ها حذف شدند!")
        return

# ---------------------- 📨 جمع‌آوری پاسخ جدید ----------------------
async def message_collector(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """جمع‌آوری پیام برای افزودن یا ویرایش"""
    user = update.effective_user
    if user.id != ADMIN_ID:
        return

    msg = update.message
    data = load_replies()
    replies = data.get("replies", {})

    # اگر در حال افزودن کلید جدید هستیم
    if context.user_data.get("reply_mode") == "add_key":
        key = msg.text.strip()
        context.user_data["reply_key"] = key
        context.user_data["reply_data"] = {"text": [], "media": []}
        context.user_data["reply_mode"] = "add_reply"

        keyboard = [
            [InlineKeyboardButton("💾 ذخیره پاسخ", callback_data="save_reply")],
            [InlineKeyboardButton("❌ لغو", callback_data="cancel")]
        ]

        await msg.reply_text(
            f"✍️ حالا پیام پاسخ برای <b>{key}</b> رو بفرست.\n"
            "می‌تونی متن، عکس، ویدیو یا صدا بفرستی.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # افزودن پاسخ به کلید
    if context.user_data.get("reply_mode") == "add_reply":
        key = context.user_data["reply_key"]
        reply_data = context.user_data["reply_data"]

        if msg.text:
            reply_data["text"].append(msg.text.strip())
        elif msg.photo:
            reply_data["media"].append(("photo", msg.photo[-1].file_id))
        elif msg.video:
            reply_data["media"].append(("video", msg.video.file_id))
        elif msg.audio:
            reply_data["media"].append(("audio", msg.audio.file_id))
        elif msg.voice:
            reply_data["media"].append(("voice", msg.voice.file_id))
        elif msg.sticker:
            reply_data["media"].append(("sticker", msg.sticker.file_id))
        elif msg.video_note:
            reply_data["media"].append(("video_note", msg.video_note.file_id))

        await msg.reply_text("✅ پیام موقتاً ذخیره شد. برای ذخیره نهایی روی 💾 بزن.")
        return

# ---------------------- 💾 ذخیره پاسخ جدید ----------------------
async def save_reply_from_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ذخیره پاسخ در فایل حافظه"""
    query = update.callback_query
    user = query.from_user
    await query.answer()

    if user.id != ADMIN_ID:
        return await query.edit_message_text("⛔ فقط مدیر اصلی مجازه!")

    data = load_replies()
    replies = data.get("replies", {})

    key = context.user_data.get("reply_key")
    reply_data = context.user_data.get("reply_data")

    if not key or not reply_data:
        return await query.edit_message_text("⚠️ هیچ پاسخی برای ذخیره وجود ندارد!")

    if key not in replies:
        replies[key] = []
    replies[key].append(reply_data)

    data["replies"] = replies
    save_replies(data)
    context.user_data.clear()

    await query.edit_message_text(f"✅ پاسخ برای '<b>{key}</b>' با موفقیت ذخیره شد!", parse_mode="HTML")

# ---------------------- 💬 پاسخ خودکار ----------------------
async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پاسخ خودکار به پیام‌های کاربر"""
    msg = update.message
    if not msg or not msg.text:
        return

    text = msg.text.strip()
    data = load_replies().get("replies", {})

    if text not in data:
        return

    entry = random.choice(data[text])
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

# ---------------------- ❌ انصراف ----------------------
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لغو عملیات جاری"""
    query = update.callback_query
    context.user_data.clear()
    await query.edit_message_text("❌ عملیات لغو شد.")# ======================= 🧭 دستور /replypanel مخصوص ADMIN =======================
from telegram.ext import CommandHandler

async def open_reply_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """باز کردن مستقیم پنل مدیریت با دستور /replypanel"""
    user = update.effective_user
    if user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه از این دستور استفاده کنه!")

    data = load_replies()
    replies = data.get("replies", {})

    keyboard = [
        [InlineKeyboardButton("➕ افزودن پاسخ جدید", callback_data="add_new")],
        [InlineKeyboardButton("📋 مشاهده پاسخ‌ها", callback_data="list_replies")]
    ]

    if replies:
        keyboard.append([InlineKeyboardButton("🗑 حذف همه پاسخ‌ها", callback_data="delete_all")])

    await update.message.reply_text(
        "🧠 <b>پنل مدیریت پاسخ‌ها (ADMIN)</b>\n"
        "از دکمه‌های زیر برای کنترل پاسخ‌ها استفاده کن 👇",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
