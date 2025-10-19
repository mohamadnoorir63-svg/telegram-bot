# ======================= 🧠 admin_panel.py (نسخه سالم و هماهنگ) =======================
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from datetime import datetime
import asyncio
import os

from memory_manager import get_stats
from bot import backup, lock_learning, unlock_learning, toggle, reload_memory, reset_memory, broadcast, cloudsync

ADMIN_ID = int(os.getenv("ADMIN_ID", "7089376754"))

# ======================= 🧩 پنل اصلی =======================
async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش پنل مدیریت فقط برای مدیر اصلی"""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه به پنل دسترسی داشته باشه!")

    keyboard = [
        [
            InlineKeyboardButton("📊 آمار", callback_data="admin:stats"),
            InlineKeyboardButton("💾 بک‌آپ", callback_data="admin:backup"),
        ],
        [
            InlineKeyboardButton("☁️ Cloud Sync", callback_data="admin:cloud"),
            InlineKeyboardButton("📢 ارسال همگانی", callback_data="admin:broadcast"),
        ],
        [
            InlineKeyboardButton("🔒 قفل یادگیری", callback_data="admin:lock"),
            InlineKeyboardButton("🔓 باز کردن یادگیری", callback_data="admin:unlock"),
        ],
        [
            InlineKeyboardButton("🧠 ریست حافظه", callback_data="admin:reset"),
            InlineKeyboardButton("⚙️ بوت مجدد", callback_data="admin:reload"),
        ],
        [
            InlineKeyboardButton("🚪 خروج از گروه", callback_data="admin:leave"),
        ]
    ]

    await update.message.reply_text(
        "👑 <b>پنل مدیریت خنگول فارسی</b>\n\nاز دکمه‌های زیر برای کنترل ربات استفاده کن:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# ======================= ⚙️ کنترل عملکرد دکمه‌ها =======================
async def admin_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split(":")[1]

    if update.effective_user.id != ADMIN_ID:
        return await query.edit_message_text("⛔ فقط مدیر اصلی مجازه!")

    if data == "stats":
        stats = get_stats()
        msg = (
            f"📊 <b>آمار فعلی ربات:</b>\n\n"
            f"🧩 جملات ذخیره‌شده: <code>{stats['phrases']}</code>\n"
            f"💬 پاسخ‌ها: <code>{stats['responses']}</code>\n"
            f"🎭 مود فعلی: <b>{stats['mode']}</b>\n"
            f"🕓 {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}"
        )
        await query.edit_message_text(msg, parse_mode="HTML")

    elif data == "backup":
        await query.edit_message_text("💾 در حال تهیه بک‌آپ...")
        await backup(update, context)
        await query.edit_message_text("✅ بک‌آپ ساخته و ارسال شد!")

    elif data == "cloud":
        await query.edit_message_text("☁️ در حال Cloud Sync...")
        await cloudsync(update, context)
        await query.edit_message_text("✅ Cloud Sync با موفقیت انجام شد!")

    elif data == "broadcast":
        context.user_data["await_broadcast"] = True
        await query.edit_message_text("📢 پیام همگانی رو بفرست:")

    elif data == "lock":
        await lock_learning(update, context)
        await query.edit_message_text("🔒 یادگیری ربات قفل شد.")

    elif data == "unlock":
        await unlock_learning(update, context)
        await query.edit_message_text("🔓 یادگیری آزاد شد.")

    elif data == "reset":
        await query.edit_message_text("♻️ در حال پاکسازی حافظه...")
        await reset_memory(update, context)

    elif data == "reload":
        await query.edit_message_text("⚙️ در حال بوت مجدد...")
        await reload_memory(update, context)

    elif data == "leave":
        await query.edit_message_text("🚪 در حال خروج از گروه...")
        await context.bot.leave_chat(update.effective_chat.id)

# ======================= 📨 ارسال همگانی =======================
async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت پیام همگانی از مدیر"""
    if not context.user_data.get("await_broadcast"):
        return
    if update.effective_user.id != ADMIN_ID:
        return

    context.user_data["await_broadcast"] = False
    await broadcast(update, context)
