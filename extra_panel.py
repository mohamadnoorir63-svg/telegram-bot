# extra_panel.py
import os
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

# مسیر فایل‌های متنی (اختیاری)
TEXTS_PATH = "texts_extra"  # می‌تونی این پوشه بسازی یا متن‌ها داخل دیکشنری بذاری

async def load_text(file_name, default_text):
    path = os.path.join(TEXTS_PATH, file_name)
    if os.path.exists(path):
        async with aiofiles.open(path, "r", encoding="utf-8") as f:
            return await f.read()
    return default_text

# ======================= نمایش پنل اصلی جانبی =======================
async def show_extra_panel(update: Update, context: ContextTypes.DEFAULT_TYPE, edit=False):
    user_name = update.effective_user.first_name
    text = f"🌟 سلام {user_name}! به پنل جانبی خوش آمدی.\nاز دکمه‌های زیر یکی را انتخاب کن:"

    keyboard = [
        [InlineKeyboardButton("💫 درباره", callback_data="extra_about")],
        [InlineKeyboardButton("🧩 قابلیت‌ها", callback_data="extra_features")],
        [InlineKeyboardButton("👨‍💻 تیم ما", callback_data="extra_team")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_main")]
    ]
    markup = InlineKeyboardMarkup(keyboard)

    if edit:
        await update.callback_query.edit_message_text(text, reply_markup=markup)
    else:
        await update.message.reply_text(text, reply_markup=markup)

# ======================= هندلر دکمه‌ها =======================
async def extra_panel_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    prefix = "extra_"
    data = query.data

    texts_dict = {
        "about": "💫 این ربات ساخته شده برای سرگرمی و مدیریت گروه‌ها!",
        "features": "🧩 قابلیت‌ها:\n- مدیریت گروه\n- ارسال پیام همگانی\n- فان و سرگرمی",
        "team": "👨‍💻 تیم ما شامل چند توسعه‌دهنده حرفه‌ای است."
    }

    if data.startswith(prefix):
        key = data.replace(prefix, "")
        text = texts_dict.get(key, "❗ محتوایی موجود نیست.")
        # دکمه بازگشت
        back_btn = [[InlineKeyboardButton("🔙 بازگشت", callback_data="extra_back")]]
        await query.edit_message_text(text + "\n\n", reply_markup=InlineKeyboardMarkup(back_btn))
    elif data == "extra_back" or data == "back_main":
        # بازگشت به منوی اصلی
        from main import show_main_panel  # فرض اینکه این تابع در main.py هست
        await show_main_panel(update, context, edit=True)
