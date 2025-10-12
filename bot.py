import asyncio
import random
import os
import sys
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from memory_manager import (
    init_files, load_data, save_data, learn, shadow_learn,
    merge_shadow_memory, get_reply, set_mode, get_stats, enhance_sentence
)

# 🔑 تنظیمات پایه
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7089376754  # آیدی مدیر
init_files()
status = {"active": True, "learning": True, "last_joke": datetime.now()}


# ========================= ✳️ دستورات =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "🤖 سلام! خنگول فارسی 6.6 اینجاست 😜\n\nبیا ببینم چی می‌خوای ازم یاد بگیری!"
    await update.message.reply_text(msg)


async def toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status["active"] = not status["active"]
    await update.message.reply_text("✅ خنگول فعال شد!" if status["active"] else "💤 خنگول خاموش شد!")


async def learn_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status["learning"] = not status["learning"]
    if status["learning"]:
        merge_shadow_memory()
        await update.message.reply_text("📚 یادگیری دوباره فعال شد!")
    else:
        await update.message.reply_text("😴 یادگیری خاموش شد (در حالت پنهان ادامه دارد!)")


async def mode_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("🎭 دستور استفاده: /mode شوخ / بی‌ادب / غمگین / نرمال")
    mood = context.args[0].lower()
    if mood in ["شوخ", "بی‌ادب", "غمگین", "نرمال"]:
        set_mode(mood)
        await update.message.reply_text(f"مود به {mood} تغییر کرد 😎")
    else:
        await update.message.reply_text("❌ مود نامعتبر است!")


async def leave_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        await update.message.reply_text("🫡 خدافظ! من رفتم ولی دلم برات تنگ میشه 😂")
        await context.bot.leave_chat(update.message.chat_id)


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_stats()
    msg = (
        f"📊 آمار خنگول:\n"
        f"• جملات یادگرفته‌شده: {data['phrases']}\n"
        f"• پاسخ‌ها: {data['responses']}\n"
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
        [InlineKeyboardButton("🧠 وضعیت یادگیری", callback_data="learn_status")],
        [InlineKeyboardButton("💤 خاموش / روشن", callback_data="toggle_bot")],
        [InlineKeyboardButton("🔁 ری‌استارت ربات", callback_data="restart_bot")],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🔧 پنل مدیریتی خنگول 6.6", reply_markup=markup)


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

    elif data == "learn_status":
        text = "✅ فعال" if status["learning"] else "🚫 غیرفعال"
        await query.edit_message_text(f"📚 وضعیت یادگیری: {text}")

    elif data == "toggle_bot":
        status["active"] = not status["active"]
        await query.edit_message_text("⚙️ وضعیت: فعال ✅" if status["active"] else "😴 خنگول خاموش شد!")

    elif data == "broadcast":
        await query.edit_message_text("✉️ پیامت رو بنویس تا به همه چت‌ها ارسال کنم:")
        context.user_data["broadcast_mode"] = True

    elif data == "restart_bot":
        await query.edit_message_text("🔁 ربات در حال ری‌استارت است ...")
        await asyncio.sleep(2)
        os.execv(sys.executable, ['python'] + sys.argv)  # ری‌استارت کامل برنامه


# ========================= 📨 ارسال همگانی =========================

async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.user_data.get("broadcast_mode"):
        return

    message = update.message.text
    context.user_data["broadcast_mode"] = False
    sent = 0
    targets = []

    try:
        groups = load_data("group_data.json")
        if isinstance(groups, dict):
            targets.extend(groups.keys())
    except:
        pass

    try:
        users = load_data("memory.json").get("users", [])
        if isinstance(users, list):
            targets.extend(users)
    except:
        pass

    for chat_id in set(targets):
        try:
            await context.bot.send_message(chat_id=chat_id, text=message)
            sent += 1
        except Exception as e:
            print(f"❌ ارسال به {chat_id} ناموفق: {e}")

    await update.message.reply_text(f"✅ پیام به {sent} چت ارسال شد!")


# ========================= 👋 خوشامدگویی و ثبت گروه =========================

async def welcome_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        await update.message.reply_text(f"🎉 خوش اومدی {member.first_name}! 😄")


async def register_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type in ["group", "supergroup"]:
        data = load_data("group_data.json")
        if str(chat.id) not in data:
            data[str(chat.id)] = {"title": chat.title}
            save_data("group_data.json", data)
            await update.message.reply_text("😜 خنگول با موفقیت در این گروه فعال شد!")


# ========================= 💬 پاسخ و یادگیری =========================

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id

    # ذخیره آی‌دی کاربر
    data = load_data("memory.json")
    if "users" not in data:
        data["users"] = []
    if user_id not in data["users"]:
        data["users"].append(user_id)
        save_data("memory.json", data)

    if not status["active"]:
        if status["learning"]:
            shadow_learn(text, "")
        return

    # شوخی خودکار
    if datetime.now() - status["last_joke"] > timedelta(hours=1):
        joke = random.choice([
            "می‌دونی فرق تو با خر چیه؟ 😜 هیچی، فقط خر مودب‌تره!",
            "من از بس با شما حرف زدم باهوش شدم 😎",
            "می‌خواستم جدی باشم ولی نمیشه با تو 😂"
        ])
        await update.message.reply_text(joke)
        status["last_joke"] = datetime.now()

    # یادگیری
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

    reply_text = get_reply(text)
    reply_text = enhance_sentence(reply_text)
    await update.message.reply_text(reply_text)


# ========================= 🚀 اجرای ربات =========================

if __name__ == "__main__":
    print("🤖 خنگول فارسی 6.6 آماده به خدمت است ...")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", admin_panel))
    app.add_handler(CommandHandler("toggle", toggle))
    app.add_handler(CommandHandler("learn", learn_mode))
    app.add_handler(CommandHandler("mode", mode_change))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("leave", leave_group))
    app.add_handler(CallbackQueryHandler(admin_callback))

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_member))
    app.add_handler(MessageHandler(filters.ALL, register_group))
    app.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_ID), broadcast_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    app.run_polling(allowed_updates=Update.ALL_TYPES, stop_signals=None)
