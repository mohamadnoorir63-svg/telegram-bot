# auto_brain/admin_panel.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
import os

ADMIN_ID = int(os.getenv("ADMIN_ID", "7089376754"))

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش پنل مدیریتی اصلی"""
    user = update.effective_user
    if user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی به پنل دسترسی دارد!")

    keyboard = [
        [
            InlineKeyboardButton("🔒 قفل یادگیری", callback_data="admin:lock"),
            InlineKeyboardButton("🔓 باز کردن یادگیری", callback_data="admin:unlock"),
        ],
        [
            InlineKeyboardButton("🧠 ریست حافظه", callback_data="admin:reset"),
            InlineKeyboardButton("🔄 ریلود مغز", callback_data="admin:reload"),
        ],
        [
            InlineKeyboardButton("💾 بک‌آپ", callback_data="admin:backup"),
            InlineKeyboardButton("☁️ کلاد سینک", callback_data="admin:cloud"),
        ],
        [
            InlineKeyboardButton("📊 آمار کلی", callback_data="admin:stats"),
            InlineKeyboardButton("🚪 خروج", callback_data="admin:leave"),
        ],
    ]
    await update.message.reply_text(
        "⚙️ پنل مدیریتی خنگول", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """واکنش به دکمه‌های پنل مدیریت"""
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user

    if user.id != ADMIN_ID:
        return await query.message.reply_text("⛔ فقط مدیر اصلی مجازه!")

    if data == "admin:lock":
        from bot import lock_learning
        await lock_learning(update, context)
    elif data == "admin:unlock":
        from bot import unlock_learning
        await unlock_learning(update, context)
    elif data == "admin:reset":
        from bot import reset_memory
        await reset_memory(update, context)
    elif data == "admin:reload":
        from bot import reload_memory
        await reload_memory(update, context)
    elif data == "admin:backup":
        from bot import backup
        await backup(update, context)
    elif data == "admin:cloud":
        from bot import cloudsync
        await cloudsync(update, context)
    elif data == "admin:stats":
        from bot import stats
        await stats(update, context)
    elif data == "admin:leave":
        from bot import leave
        await leave(update, context)
    else:
        await query.message.reply_text("❌ گزینه نامعتبر یا پشتیبانی‌نشده.")
