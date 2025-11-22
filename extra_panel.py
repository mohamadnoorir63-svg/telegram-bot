# extra_panel.py
import os
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

# شناسه ادمین اصلی
ADMIN_ID = 8588347189  # <--- این را با آیدی خودت جایگزین کن

# دیتای نمونه دکمه‌ها و محتوای پیوی
user_panel_buttons = [
    {"text": "💬 تماس با پشتیبانی", "callback": "user_support"},
    {"text": "🎁 هدیه روزانه", "callback": "user_daily"},
]

admin_panel_buttons = [
    {"text": "➕ افزودن دکمه", "callback": "admin_add_btn"},
    {"text": "📝 ویرایش دکمه‌ها", "callback": "admin_edit_btn"},
    {"text": "🗑 حذف دکمه", "callback": "admin_del_btn"},
]

# ======================= نمایش پنل پیوی برای کاربران عادی =======================
async def show_user_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(btn["text"], callback_data=f"user_{btn['callback']}")] for btn in user_panel_buttons]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🌟 پنل پیوی شما:\nاز دکمه‌ها استفاده کنید:", reply_markup=markup)

# ======================= نمایش پنل مدیریت برای ادمین =======================
async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط ادمین مجاز است!")

    keyboard = [[InlineKeyboardButton(btn["text"], callback_data=f"admin_{btn['callback']}")] for btn in admin_panel_buttons]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("⚙️ پنل مدیریت ربات:\nاز دکمه‌ها استفاده کنید:", reply_markup=markup)

# ======================= هندلر دکمه‌ها =======================
async def extra_panel_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("user_"):
        key = data.replace("user_", "")
        if key == "support":
            await query.edit_message_text("📬 برای پشتیبانی با @SupportUser تماس بگیرید.")
        elif key == "daily":
            await query.edit_message_text("🎁 شما امروز ۵ سکه دریافت کردید!")
        else:
            await query.edit_message_text("❗ عملکرد نامشخص.")
    elif data.startswith("admin_"):
        key = data.replace("admin_", "")
        if key == "add_btn":
            await query.edit_message_text("➕ برای افزودن دکمه جدید دستور خود را ارسال کنید...")
        elif key == "edit_btn":
            await query.edit_message_text("📝 برای ویرایش دکمه‌ها، روی دکمه موردنظر کلیک کنید...")
        elif key == "del_btn":
            await query.edit_message_text("🗑 برای حذف دکمه‌ها، روی دکمه موردنظر کلیک کنید...")
        else:
            await query.edit_message_text("❗ عملکرد نامشخص.")
