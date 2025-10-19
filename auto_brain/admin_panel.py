# ======================= 🧠 admin_panel.py (نسخه نهایی بدون import از bot.py) =======================
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from datetime import datetime
import asyncio
import os
from memory_manager import get_stats
from auto_brain.auto_backup import cloudsync_internal

# 💡 مقدار ADMIN_ID مستقیم از محیط گرفته می‌شود
ADMIN_ID = int(os.getenv("ADMIN_ID", "7089376754"))

# ======================= 🧩 پنل اصلی =======================
async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش پنل مدیریت برای مدیر اصلی"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")

    keyboard = [
        [
            InlineKeyboardButton("📊 آمار", callback_data="admin:stats"),
            InlineKeyboardButton("💾 بک‌آپ کامل", callback_data="admin:backup"),
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

    # 📊 آمار
    if data == "stats":
        stats = get_stats()
        msg = (
            f"📊 <b>آمار فعلی ربات:</b>\n\n"
            f"🧩 جملات ذخیره‌شده: <code>{stats['phrases']}</code>\n"
            f"💬 پاسخ‌ها: <code>{stats['responses']}</code>\n"
            f"🎭 مود فعلی: <b>{stats['mode']}</b>\n"
            f"🕓 {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}"
        )
        return await query.edit_message_text(msg, parse_mode="HTML")

    # 💾 بک‌آپ
    elif data == "backup":
        from bot import backup  # فقط تابع async در زمان کلیک import می‌شود
        await query.edit_message_text("💾 در حال تهیه بک‌آپ...")
        await backup(update, context)
        return await query.edit_message_text("✅ بک‌آپ ساخته و ارسال شد!")

    # ☁️ Cloud Sync
    elif data == "cloud":
        await query.edit_message_text("☁️ در حال Cloud Sync...")
        await cloudsync_internal(context.bot)
        return await query.edit_message_text("✅ Cloud Sync انجام شد!")

    # 📢 ارسال همگانی
    elif data == "broadcast":
        from bot import broadcast
        context.user_data["await_broadcast"] = True
        return await query.edit_message_text("📢 پیام همگانی رو بفرست:")

    # 🔒 قفل یادگیری
    elif data == "lock":
        from bot import lock_learning
        await lock_learning(update, context)
        return await query.edit_message_text("🔒 یادگیری قفل شد!")

    # 🔓 باز کردن یادگیری
    elif data == "unlock":
        from bot import unlock_learning
        await unlock_learning(update, context)
        return await query.edit_message_text("🔓 یادگیری آزاد شد!")

    # ♻️ ریست حافظه
    elif data == "reset":
        from bot import reset_memory
        await query.edit_message_text("♻️ در حال پاکسازی حافظه...")
        await reset_memory(update, context)
        return

    # ⚙️ بوت مجدد
    elif data == "reload":
        from bot import reload_memory
        await query.edit_message_text("⚙️ در حال بوت مجدد سیستم...")
        await reload_memory(update, context)
        return

# ======================= 📨 ارسال همگانی =======================
async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت پیام همگانی از مدیر"""
    if not context.user_data.get("await_broadcast"):
        return
    if update.effective_user.id != ADMIN_ID:
        return

    from bot import broadcast
    context.user_data["await_broadcast"] = False
    await broadcast(update, context)
