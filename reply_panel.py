# ========================= ✳️ Reply Panel Manager =========================
# نسخه هماهنگ با Khenqol Cloud+ Supreme Pro 8.5.1
# پشتیبانی از افزودن، حذف، و پاسخ خودکار + فرمت ریپلای و "="

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
import json
import os
import random

REPLY_FILE = "memory.json"

# ---------------------- 📂 توابع کمکی ----------------------
def load_replies():
    """خواندن پاسخ‌ها از فایل memory.json"""
    if not os.path.exists(REPLY_FILE):
        return {"replies": {}}
    with open(REPLY_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            return data if "replies" in data else {"replies": {}}
        except:
            return {"replies": {}}


def save_replies(data):
    """ذخیره پاسخ‌ها در فایل memory.json"""
    with open(REPLY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------------------- 🎯 افزودن پاسخ ----------------------
async def add_reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """افزودن پاسخ جدید — پشتیبانی از ریپلای و فرمت <کلید>=<پاسخ>"""
    message = update.message
    text = message.text.strip().replace("افزودن پاسخ", "").strip()
    data = load_replies()
    replies = data.get("replies", {})

    # حالت ۱: افزودن پاسخ <کلید>=<پاسخ>
    if "=" in text:
        try:
            key, reply_text = text.split("=", 1)
            key, reply_text = key.strip(), reply_text.strip()
            if not key or not reply_text:
                raise ValueError
        except:
            return await message.reply_text("❗ استفاده صحیح: افزودن پاسخ <نام>=<پاسخ>")

        if key not in replies:
            replies[key] = []
        if reply_text not in replies[key]:
            replies[key].append(reply_text)
            save_replies(data)
            return await message.reply_text(f"✅ پاسخ برای '{key}' ذخیره شد!\n💬 {reply_text}")
        else:
            return await message.reply_text("⚠️ این پاسخ از قبل وجود دارد!")

    # حالت ۲: ریپلای روی پیام متنی
    if message.reply_to_message and text:
        key = text
        reply_text = message.reply_to_message.text.strip() if message.reply_to_message.text else ""
        if not reply_text:
            return await message.reply_text("❗ باید روی یک پیام متنی ریپلای بزنی!")

        if key not in replies:
            replies[key] = []
        if reply_text not in replies[key]:
            replies[key].append(reply_text)
            save_replies(data)
            return await message.reply_text(f"✅ پاسخ برای '{key}' ذخیره شد!\n💬 {reply_text}")
        else:
            return await message.reply_text("⚠️ این پاسخ از قبل وجود دارد!")

    # حالت ۳: بدون پارامتر معتبر → نمایش راهنما
    return await message.reply_text(
        "❗ استفاده صحیح:\n"
        "1️⃣ افزودن پاسخ <نام>=<پاسخ>\n"
        "2️⃣ یا روی پیام متنی ریپلای بزن و بنویس:\n"
        "افزودن پاسخ <نام>"
    )


# ---------------------- 🗑 حذف پاسخ ----------------------
async def delete_reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف تمام پاسخ‌های یک کلید"""
    if not context.args:
        return await update.message.reply_text("❗ استفاده صحیح: حذف پاسخ <نام>")

    key = " ".join(context.args).strip()
    data = load_replies()
    replies = data.get("replies", {})

    if key in replies:
        del replies[key]
        save_replies(data)
        await update.message.reply_text(f"🗑 تمام پاسخ‌های '{key}' حذف شدند.")
    else:
        await update.message.reply_text(f"⚠️ پاسخی با نام '{key}' پیدا نشد.")


# ---------------------- 💬 پاسخ خودکار ----------------------
async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال پاسخ در صورت وجود کلید در memory.json"""
    text = update.message.text.strip()
    data = load_replies()
    replies = data.get("replies", {})   # ← اصلاح‌شده (نه دوباره get روی data)

    if text in replies:
        options = replies[text]
        if options:
            reply = random.choice(options)
            await update.message.reply_text(reply)


# ---------------------- 🧮 پشتیبانی از پنل قدیمی (در صورت فعال بودن) ----------------------
async def message_collector(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """جمع‌آوری پاسخ‌ها تا وقتی ذخیره زده شود"""
    if "reply_key" not in context.user_data:
        return

    key = context.user_data["reply_key"]
    text = update.message.text.strip()

    if "reply_temp" not in context.user_data:
        context.user_data["reply_temp"] = []
    context.user_data["reply_temp"].append(text)

    await update.message.reply_text(f"✅ پاسخ موقت برای '{key}' ذخیره شد.")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت دکمه‌های پنل (برای حالت دستی قدیمی)"""
    query = update.callback_query
    await query.answer()

    data = load_replies()
    replies = data.get("replies", {})
    key = context.user_data.get("reply_key")

    if not key:
        return await query.edit_message_text("❌ هیچ کلیدی انتخاب نشده.")

    if query.data == "add_random":
        temp = context.user_data.get("reply_temp", [])
        if not temp:
            return await query.answer("⚠️ هنوز پاسخی اضافه نکردی!", show_alert=True)

        replies.setdefault(key, [])
        for t in temp:
            if t not in replies[key]:
                replies[key].append(t)

        save_replies(data)
        context.user_data["reply_temp"] = []
        await query.edit_message_text(f"🎲 پاسخ‌های تصادفی برای '{key}' ثبت شدند ✅")

    elif query.data == "save_reply":
        temp = context.user_data.get("reply_temp", [])
        if not temp:
            return await query.answer("⚠️ پاسخی برای ذخیره نیست!", show_alert=True)

        replies.setdefault(key, [])
        for t in temp:
            if t not in replies[key]:
                replies[key].append(t)

        save_replies(data)
        context.user_data.clear()
        await query.edit_message_text(f"✅ پاسخ برای '{key}' ذخیره شد و پنل بسته شد.")

    elif query.data == "delete_reply":
        if key in replies:
            del replies[key]
            save_replies(data)
            await query.edit_message_text(f"🗑 تمام پاسخ‌های '{key}' حذف شدند.")
        else:
            await query.answer("⚠️ پاسخی برای حذف وجود ندارد!")
