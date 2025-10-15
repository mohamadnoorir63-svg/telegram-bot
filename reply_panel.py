import json
import os
import random
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

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
    """اجرای دستور افزودن پاسخ <کلید>"""
    if not context.args:
        return await update.message.reply_text("❗ استفاده صحیح: افزودن پاسخ <نام>")

    key = " ".join(context.args).strip()
    data = load_replies()
    replies = data.get("replies", {})

    # اگر هنوز پاسخی برایش وجود ندارد، ایجاد کن
    if key not in replies:
        replies[key] = []
        save_replies(data)

    # ذخیره در حافظه موقت تا بعد از انتخاب تنظیمات ذخیره شود
    context.user_data["reply_key"] = key
    context.user_data["reply_temp"] = []

    keyboard = [
        [
            InlineKeyboardButton("🎲 افزودن پاسخ تصادفی", callback_data="add_random"),
        ],
        [
            InlineKeyboardButton("💾 ذخیره", callback_data="save_reply"),
            InlineKeyboardButton("🗑 حذف", callback_data="delete_reply"),
        ]
    ]
    await update.message.reply_text(
        f"🧠 حالت افزودن پاسخ فعال شد برای:\n👉 <b>{key}</b>\n\n"
        "متن‌هایی که می‌خوای ذخیره بشن رو بفرست (هر پیام = یک پاسخ)\n"
        "وقتی تموم شد روی «💾 ذخیره» بزن.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ---------------------- 📨 ذخیره پاسخ ----------------------
async def message_collector(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """جمع‌آوری پاسخ‌ها تا وقتی ذخیره زده شود"""
    if "reply_key" not in context.user_data:
        return  # در حالت افزودن نیست

    key = context.user_data["reply_key"]
    text = update.message.text.strip()

    # اضافه به لیست موقت
    if "reply_temp" not in context.user_data:
        context.user_data["reply_temp"] = []
    context.user_data["reply_temp"].append(text)

    await update.message.reply_text(f"✅ پاسخ موقت ذخیره شد برای '{key}'")


# ---------------------- 🧮 دکمه‌ها ----------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = load_replies()
    replies = data.get("replies", {})
    key = context.user_data.get("reply_key")

    if not key:
        return await query.edit_message_text("❌ هیچ کلیدی انتخاب نشده.")

    # افزودن پاسخ تصادفی (از موقت)
    if query.data == "add_random":
        temp = context.user_data.get("reply_temp", [])
        if not temp:
            return await query.answer("⚠️ هنوز پاسخی اضافه نکردی!", show_alert=True)

        if key not in replies:
            replies[key] = []

        for t in temp:
            if t not in replies[key]:
                replies[key].append(t)

        save_replies(data)
        context.user_data["reply_temp"] = []
        await query.edit_message_text(f"🎲 پاسخ‌های تصادفی برای '{key}' ثبت شدند ✅")

    # ذخیره همه پاسخ‌ها
    elif query.data == "save_reply":
        temp = context.user_data.get("reply_temp", [])
        if not temp:
            return await query.answer("⚠️ پاسخی برای ذخیره نیست!", show_alert=True)

        if key not in replies:
            replies[key] = []

        for t in temp:
            if t not in replies[key]:
                replies[key].append(t)

        save_replies(data)
        context.user_data.clear()
        await query.edit_message_text(f"✅ پاسخ برای '{key}' ذخیره شد و پنل بسته شد.")

    # حذف کل پاسخ
    elif query.data == "delete_reply":
        if key in replies:
            del replies[key]
            save_replies(data)
            await query.edit_message_text(f"🗑 تمام پاسخ‌های '{key}' حذف شدند.")
        else:
            await query.answer("⚠️ پاسخی برای حذف وجود ندارد!")


# ---------------------- 💬 استفاده از پاسخ‌ها ----------------------
async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال پاسخ هنگام تطابق"""
    text = update.message.text.strip()
    data = load_replies().get("replies", {})

    if text in data:
        options = data[text]
        if not options:
            return
        reply = random.choice(options)
        await update.message.reply_text(reply)
