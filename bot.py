import asyncio
import random
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from memory_manager_sqlite import (
    init_db, learn, get_reply, set_mode,
    get_stats, enhance_sentence,
    register_group, get_all_groups
)

# 🧠 تنظیمات
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7089376754
init_db()  # ایجاد جداول در دیتابیس

# وضعیت ربات
status = {"active": True, "learning": True, "last_joke": datetime.now()}


# ========================= ✳️ دستورات فارسی =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    msg = f"😜 نصب خنگول با موفقیت انجام شد!\n\nسلام {update.effective_user.first_name} خوش اومدی به جمع خنگولا 😂"
    if chat.type in ["group", "supergroup"]:
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("سلام رفیق 😎 من خنگولم! بگو چی یاد بگیرم؟")


async def toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status["active"] = not status["active"]
    text = "✅ خنگول روشن شد!" if status["active"] else "💤 خنگول خاموش شد!"
    await update.message.reply_text(text)


async def mode_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.replace("مود", "").strip()
    mood = text.lower()
    valid_modes = {"شوخ", "بی‌ادب", "غمگین", "نرمال"}

    if mood in valid_modes:
        set_mode(mood)
        await update.message.reply_text(f"🎭 مود به '{mood}' تغییر کرد 😎")
    else:
        await update.message.reply_text("❌ مود نامعتبره! فقط از شوخ، بی‌ادب، غمگین یا نرمال استفاده کن.")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_stats()
    msg = (
        f"📊 آمار خنگول:\n"
        f"• جملات یادگرفته‌شده: {data['phrases']}\n"
        f"• تعداد پاسخ‌ها: {data['responses']}\n"
        f"• مود فعلی: {data['mode']}\n"
    )
    await update.message.reply_text(msg)


# ========================= ⚙️ پنل مدیر =========================

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه وارد پنل بشه!")

    keyboard = [
        [InlineKeyboardButton("📨 ارسال همگانی", callback_data="broadcast")],
        [InlineKeyboardButton("📊 آمار", callback_data="stats")],
        [InlineKeyboardButton("💤 روشن / خاموش", callback_data="toggle_bot")],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🔧 پنل مدیریتی خنگول", reply_markup=markup)


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "stats":
        s = get_stats()
        await query.edit_message_text(
            f"📈 آمار خنگول:\n"
            f"جملات: {s['phrases']}\nپاسخ‌ها: {s['responses']}\nمود فعلی: {s['mode']}"
        )
    elif data == "toggle_bot":
        status["active"] = not status["active"]
        await query.edit_message_text("⚙️ فعال ✅" if status["active"] else "😴 خاموش شد!")
    elif data == "broadcast":
        await query.edit_message_text("پیامت رو بنویس تا به همه گروه‌ها بفرستم:")
        context.user_data["broadcast_mode"] = True


# ========================= 📨 ارسال همگانی =========================

async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.user_data.get("broadcast_mode"):
        return

    message = update.message.text
    context.user_data["broadcast_mode"] = False

    groups = get_all_groups()
    sent = 0
    for chat_id in groups:
        try:
            await context.bot.send_message(chat_id=chat_id, text=message)
            sent += 1
        except Exception as e:
            print(f"❌ ارسال به {chat_id} ناموفق: {e}")

    await update.message.reply_text(f"✅ پیام به {sent} گروه ارسال شد!")


# ========================= 💬 پاسخ‌دهی =========================

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # دستورات ساده
    if text == "روشن شو":
        status["active"] = True
        await update.message.reply_text("✅ خنگول روشن شد!")
        return
    elif text == "خاموش شو":
        status["active"] = False
        await update.message.reply_text("💤 خنگول خاموش شد!")
        return
    elif text == "مود":
        await mode_change(update, context)
        return
    elif text == "آمار":
        await stats(update, context)
        return
    elif text == "پنل":
        await admin_panel(update, context)
        return

    # اگر خاموشه → هیچ کاری نکن
    if not status["active"]:
        return

    # شوخی خودکار هر ساعت
    if datetime.now() - status["last_joke"] > timedelta(hours=1):
        joke = random.choice([
            "می‌دونی فرق تو با خر چیه؟ 😜 هیچی، فقط خر مودب‌تره!",
            "من از بس با شما حرف زدم، دارم دانشمند میشم 😎",
            "می‌خواستم جدی باشم ولی با تو نمیشه 😂"
        ])
        await update.message.reply_text(joke)
        status["last_joke"] = datetime.now()

    # یادگیری دستی
    if text.startswith("یادبگیر "):
        parts = text.replace("یادبگیر ", "").split("\n")
        if len(parts) > 1:
            phrase = parts[0].strip()
            responses = [p.strip() for p in parts[1:] if p.strip()]
            for r in responses:
                learn(phrase, r)
            await update.message.reply_text(f"🧠 یاد گرفتم {len(responses)} پاسخ برای '{phrase}'!")
        else:
            await update.message.reply_text("❗ بعد از 'یادبگیر' بنویس جمله و پاسخ‌هاش رو با خط جدید جدا کن.")
        return

    # پاسخ معمولی
    reply_text = get_reply(text)
    reply_text = enhance_sentence(reply_text)
    await update.message.reply_text(reply_text)


# 🚀 اجرای ربات
if __name__ == "__main__":
    print("🤖 خنگول فارسی 6.1 (نسخه SQLite) آماده به خدمت است ...")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, lambda u, c: register_group(u.effective_chat.id, u.effective_chat.title)))
    app.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_ID), broadcast_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))
    app.add_handler(CallbackQueryHandler(admin_callback))

    app.run_polling(stop_signals=None, timeout=120)
