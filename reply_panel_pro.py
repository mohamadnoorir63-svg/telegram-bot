# ========================= ✳️ Reply Panel Pro++ 8.5.4 =========================
# نسخه جدید با پشتیبانی از چند پاسخ، حالت تصادفی و ویرایش پاسخ تکی
# مخصوص ربات خنگول Cloud+ Supreme Pro Stable+
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
        [InlineKeyboardButton("💾 ذخیره پاسخ جدید", callback_data="save_reply")],
        [InlineKeyboardButton("❌ انصراف", callback_data="cancel_reply")]
    ]

    await message.reply_text(
        f"🧠 در حال افزودن پاسخ برای: <b>{text}</b>\n"
        "می‌تونی چند پیام (متن یا مدیا) بفرستی.\n"
        "در پایان روی 💾 بزن تا ذخیره شه.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------------- 📨 ذخیره پیام‌ها ----------------------
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

    await msg.reply_text("✅ پیام موقتاً ذخیره شد. بعد از اتمام، روی 💾 بزن.")

# ---------------------- 🧮 کنترل دکمه‌ها ----------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_replies()
    replies = data.get("replies", {})

    # انصراف
    if query.data == "cancel_reply":
        context.user_data.clear()
        return await query.edit_message_text("❌ عملیات لغو شد.")

    # 💾 ذخیره پاسخ جدید
    if query.data == "save_reply":
        key = context.user_data.get("reply_key")
        reply_data = context.user_data.get("reply_data")

        if not key or not reply_data:
            return await query.edit_message_text("⚠️ پاسخی برای ذخیره وجود ندارد!")

        if key not in replies:
            replies[key] = []

        replies[key].append(reply_data)
        data["replies"] = replies
        save_replies(data)
        context.user_data.clear()

        return await query.edit_message_text(f"✅ پاسخ جدید برای '{key}' ذخیره شد!")

    # ✏️ ذخیره ویرایش پاسخ تکی
    if query.data.startswith("save_edit_"):
        key, index = query.data.replace("save_edit_", "").split("_")
        index = int(index)
        reply_data = context.user_data.get("reply_data")

        if not reply_data:
            return await query.edit_message_text("⚠️ پاسخی برای ذخیره وجود ندارد!")

        replies[key][index] = reply_data
        save_replies(data)
        context.user_data.clear()
        return await query.edit_message_text(f"✅ پاسخ شماره {index+1} برای '{key}' ویرایش شد!")

    # 🗑 حذف پاسخ تکی
    if query.data.startswith("del_item_"):
        key, index = query.data.replace("del_item_", "").split("_")
        index = int(index)

        if key in replies and index < len(replies[key]):
            del replies[key][index]
            if not replies[key]:
                del replies[key]
            save_replies(data)
            return await query.edit_message_text(f"🗑 پاسخ شماره {index+1} از '{key}' حذف شد!")
        return await query.edit_message_text("⚠️ پاسخ مورد نظر یافت نشد.")

    # 🗑 حذف کامل کلید
    if query.data.startswith("delete_"):
        key = query.data.replace("delete_", "")
        if key in replies:
            del replies[key]
            save_replies(data)
            return await query.edit_message_text(f"🗑 تمام پاسخ‌های '{key}' حذف شدند.")
        return await query.edit_message_text("⚠️ کلید یافت نشد.")

# ---------------------- 🧭 مدیریت پاسخ‌ها ----------------------
async def manage_replies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لیست همه‌ی کلیدها"""
    data = load_replies().get("replies", {})
    if not data:
        return await update.message.reply_text("ℹ️ هنوز پاسخی ثبت نشده.")

    keyboard = []
    for key in data.keys():
        keyboard.append([
            InlineKeyboardButton(f"📋 {key}", callback_data=f"preview_{key}"),
            InlineKeyboardButton("✏️ ویرایش", callback_data=f"edit_{key}"),
            InlineKeyboardButton("🗑 حذف", callback_data=f"delete_{key}")
        ])

    await update.message.reply_text(
        "🧩 لیست پاسخ‌های ذخیره‌شده:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------------- ✏️ باز کردن منوی ویرایش ----------------------
async def start_edit_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ویرایش پاسخ تکی از یک کلید"""
    query = update.callback_query
    key = query.data.replace("edit_", "")
    data = load_replies().get("replies", {})

    if key not in data:
        return await query.edit_message_text("⚠️ پاسخی پیدا نشد!")

    keyboard = []
    preview = f"✏️ <b>{key}</b> — پاسخ‌ها:\n\n"
    for i, r in enumerate(data[key]):
        text_preview = "\n".join(r.get("text", [])) or "— بدون متن —"
        preview += f"{i+1}. {text_preview}\n"
        keyboard.append([
            InlineKeyboardButton("✏️ ویرایش", callback_data=f"edit_item_{key}_{i}"),
            InlineKeyboardButton("🗑 حذف", callback_data=f"del_item_{key}_{i}")
        ])

    await query.edit_message_text(
        preview,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------------- 💬 پاسخ خودکار ----------------------
async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال پاسخ هنگام دریافت کلید ذخیره‌شده"""
    msg = update.message
    if not msg or not msg.text:
        return

    text = msg.text.strip()
    data = load_replies().get("replies", {})
    if text not in data:
        return

    entry = random.choice(data[text])  # 🎲 انتخاب تصادفی از بین چند پاسخ
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
