# ======================= 🧠 admin_panel.py =======================
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from datetime import datetime
import asyncio
import os

ADMIN_ID = 7089376754  # آیدی عددی تو (سودو اصلی)

# ======================= 🧩 پنل اصلی =======================

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش منوی مدیریت اصلی"""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")

    keyboard = [
        [
            InlineKeyboardButton("📊 آمار", callback_data="admin:stats"),
            InlineKeyboardButton("🧠 حافظه", callback_data="admin:memory"),
        ],
        [
            InlineKeyboardButton("💾 بک‌آپ", callback_data="admin:backup"),
            InlineKeyboardButton("☁️ Cloud Sync", callback_data="admin:cloudsync"),
        ],
        [
            InlineKeyboardButton("📢 ارسال همگانی", callback_data="admin:broadcast"),
            InlineKeyboardButton("♻️ ریست حافظه", callback_data="admin:reset"),
        ],
        [
            InlineKeyboardButton("🔒 قفل یادگیری", callback_data="admin:lock"),
            InlineKeyboardButton("🔓 باز کردن یادگیری", callback_data="admin:unlock"),
        ],
        [
            InlineKeyboardButton("💬 پاسخ‌دهی روشن/خاموش", callback_data="admin:toggle_reply"),
        ],
        [
            InlineKeyboardButton("🛠 راه‌اندازی دوباره", callback_data="admin:restart"),
        ]
    ]

    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👑 <b>پنل مدیریت ربات خنگول</b>\n\n"
        "از دکمه‌های زیر برای مدیریت کامل استفاده کن:",
        reply_markup=markup,
        parse_mode="HTML"
    )

# ======================= ⚙️ کنترل عملکرد دکمه‌ها =======================

async def admin_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت عملکرد دکمه‌های پنل مدیریت"""
    query = update.callback_query
    await query.answer()
    data = query.data.split(":")[1]

    if update.effective_user.id != ADMIN_ID:
        return await query.edit_message_text("⛔ فقط مدیر اصلی می‌تونه از این پنل استفاده کنه!")

    # 📊 آمار
    if data == "stats":
        total_groups = context.bot_data.get("groups_count", 0)
        total_users = context.bot_data.get("users_count", 0)
        msg = (
            f"📊 <b>آمار فعلی ربات:</b>\n\n"
            f"👥 گروه‌ها: <code>{total_groups}</code>\n"
            f"🙍 کاربران: <code>{total_users}</code>\n"
            f"🕒 زمان: <code>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</code>"
        )
        await query.edit_message_text(msg, parse_mode="HTML")

    # 💾 بک‌آپ
    elif data == "backup":
        from auto_brain.auto_backup import create_backup
        await query.edit_message_text("⏳ در حال ساخت بک‌آپ...")
        create_backup()
        await asyncio.sleep(2)
        await query.edit_message_text("✅ بک‌آپ ساخته و ارسال شد!")

    # ☁️ Cloud Sync
    elif data == "cloudsync":
        from auto_brain.auto_backup import cloudsync_internal
        await query.edit_message_text("☁️ در حال همگام‌سازی ابری...")
        await cloudsync_internal(context.bot)
        await query.edit_message_text("✅ Cloud Sync با موفقیت انجام شد!")

    # 📢 ارسال همگانی
    elif data == "broadcast":
        context.user_data["await_broadcast"] = True
        await query.edit_message_text("📢 پیام همگانی را بفرست تا برای همه ارسال شود.")

    # ♻️ ریست حافظه
    elif data == "reset":
        from memory_manager import reset_memory
        reset_memory()
        await query.edit_message_text("♻️ حافظه با موفقیت ریست شد!")

    # 🔒 قفل / 🔓 باز کردن یادگیری
    elif data == "lock":
        from memory_manager import lock_learning
        lock_learning()
        await query.edit_message_text("🔒 یادگیری ربات قفل شد.")

    elif data == "unlock":
        from memory_manager import unlock_learning
        unlock_learning()
        await query.edit_message_text("🔓 یادگیری ربات آزاد شد.")

    # 💬 خاموش/روشن پاسخ‌دهی
    elif data == "toggle_reply":
        from config_manager import toggle_reply_mode
        toggle_reply_mode()
        await query.edit_message_text("💬 حالت پاسخ‌دهی تغییر کرد.")

    # 🛠 ری‌استارت
    elif data == "restart":
        await query.edit_message_text("♻️ در حال راه‌اندازی مجدد...")
        os.system("kill 1")

# ======================= 📨 ارسال همگانی =======================

async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت پیام همگانی از مدیر"""
    if not context.user_data.get("await_broadcast"):
        return
    if update.effective_user.id != ADMIN_ID:
        return

    text = update.message.text or None
    media = update.message.photo or update.message.video or update.message.document or None

    if not text and not media:
        return await update.message.reply_text("⚠️ فقط پیام یا مدیا بفرست.")

    await update.message.reply_text("📡 در حال ارسال پیام به همه گروه‌ها و کاربران...")

    # فرض: لیست گروه‌ها و کاربران در فایل یا دیتاست
    # می‌تونی بعداً اینجا سیستم دیتابیس اضافه کنی
    sent = 0
    for chat_id in context.bot_data.get("broadcast_targets", []):
        try:
            if text:
                await context.bot.send_message(chat_id=chat_id, text=text)
            elif media:
                if update.message.photo:
                    await context.bot.send_photo(chat_id=chat_id, photo=update.message.photo[-1].file_id, caption=update.message.caption or "")
                elif update.message.video:
                    await context.bot.send_video(chat_id=chat_id, video=update.message.video.file_id, caption=update.message.caption or "")
                elif update.message.document:
                    await context.bot.send_document(chat_id=chat_id, document=update.message.document.file_id, caption=update.message.caption or "")
            sent += 1
            await asyncio.sleep(0.1)
        except:
            pass

    await update.message.reply_text(f"✅ پیام همگانی برای {sent} چت ارسال شد.")
    context.user_data["await_broadcast"] = False
