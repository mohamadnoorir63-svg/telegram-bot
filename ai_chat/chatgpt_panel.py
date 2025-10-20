from openai import OpenAI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import os, datetime

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# کاربران فعال و امتیازشان
user_data = {}

# 🎯 نمایش دکمه‌ی ChatGPT در منو
async def show_ai_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🧠 شروع گفتگو با هوش مصنوعی", callback_data="start_ai_chat")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🤖 بخش گفتگوی ChatGPT آماده‌ست!\nبرای شروع روی دکمه زیر بزن 👇",
        reply_markup=reply_markup
    )

# 🎯 شروع گفتگوی ChatGPT
async def start_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    await query.answer()

    user_data[chat_id] = {
        "active": True,
        "limit": 5,
        "used": 0,
        "last_reset": datetime.date.today()
    }

    await query.edit_message_text(
        "🧠 گفتگوی ChatGPT فعال شد!\n"
        "می‌تونی تا ۵ پیام رایگان بفرستی.\n\n"
        "برای بستن بنویس: خاموش 🔕"
    )

# 🎯 توقف گفتگو
async def stop_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in user_data:
        user_data[chat_id]["active"] = False
    await update.message.reply_text("🔕 گفتگوی ChatGPT بسته شد.")

# 🎯 پردازش پیام‌های کاربران
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text

    # فقط در پیوی کار کنه
    if update.effective_chat.type != "private":
        return

    # بررسی وضعیت کاربر
    data = user_data.get(chat_id)
    if not data or not data["active"]:
        return  # کاربر فعال نیست

    # بررسی محدودیت روزانه
    if data["last_reset"] != datetime.date.today():
        data["used"] = 0
        data["last_reset"] = datetime.date.today()

    if data["used"] >= data["limit"]:
        await update.message.reply_text("⚠️ امتیاز امروزت تموم شد! فردا دوباره امتحان کن 😊")
        data["active"] = False
        return

    try:
        # افزایش شمارش
        data["used"] += 1

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": text}],
        )
        reply_text = response.choices[0].message.content.strip()
        await update.message.reply_text(reply_text)

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در پاسخ از ChatGPT:\n{e}")
