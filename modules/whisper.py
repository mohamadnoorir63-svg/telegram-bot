import json
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CommandHandler, CallbackQueryHandler, filters

# مسیر ذخیره نجواها
WHISPER_FILE = "whispers.json"

# ساخت فایل اگر وجود نداشت
if not os.path.exists(WHISPER_FILE):
    with open(WHISPER_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

def load_whispers():
    try:
        with open(WHISPER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_whispers(data):
    with open(WHISPER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# مراحل گفتگو
ASK_USER, ASK_MESSAGE = range(2)

async def start_whisper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع فرآیند نجوا"""
    await update.message.reply_text("🕵️ لطفاً آیدی یا نام کاربری فرد مورد نظر رو بنویس (بدون @):")
    return ASK_USER

async def ask_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """گرفتن آیدی هدف"""
    context.user_data["whisper_target"] = update.message.text.strip()
    await update.message.reply_text("✍️ حالا متنی که می‌خوای نجوا بشه رو بنویس:")
    return ASK_MESSAGE

async def receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ثبت و ارسال نجوا"""
    sender = update.effective_user
    text = update.message.text.strip()
    target_username = context.user_data.get("whisper_target")
    chat_id = update.effective_chat.id

    # جستجو در گروه برای یافتن کاربر هدف
    try:
        target_member = await context.bot.get_chat_member(chat_id, target_username)
        target_user = target_member.user
    except:
        # شاید نام کاربریه نه آیدی
        try:
            members = await context.bot.get_chat_administrators(chat_id)
            target_user = None
            for m in members:
                if m.user.username and m.user.username.lower() == target_username.lower():
                    target_user = m.user
                    break
        except:
            target_user = None

    if not target_user:
        await update.message.reply_text("⚠️ کاربر مورد نظر در گروه پیدا نشد.")
        return ConversationHandler.END

    # ساخت دیکشنری نجوا
    whispers = load_whispers()
    whisper_id = f"{chat_id}_{sender.id}_{target_user.id}_{len(whispers)+1}"

    whispers[whisper_id] = {
        "from": sender.id,
        "to": target_user.id,
        "text": text,
        "chat": chat_id
    }
    save_whispers(whispers)

    # پیام اعلام نجوا در گروه
    button = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton(f"📩 مشاهده نجوا برای {target_user.first_name}", callback_data=f"whisper:{whisper_id}")
    )

    await update.message.reply_html(
        f"🤫 <b>{target_user.first_name}</b> شما یک نجوا از طرف <b>{sender.first_name}</b> دارید!",
        reply_markup=button
    )

    # حذف خودکار نجوا بعد از 5 دقیقه
    async def auto_delete():
        await asyncio.sleep(300)
        data = load_whispers()
        if whisper_id in data:
            del data[whisper_id]
            save_whispers(data)

    asyncio.create_task(auto_delete())
    return ConversationHandler.END

async def open_whisper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """باز کردن نجوا فقط برای گیرنده"""
    query = update.callback_query
    await query.answer()
    whisper_id = query.data.split(":")[1]
    whispers = load_whispers()

    whisper = whispers.get(whisper_id)
    if not whisper:
        return await query.message.reply_text("⚠️ این نجوا منقضی شده یا حذف شده.")

    if query.from_user.id != whisper["to"]:
        return await query.message.reply_text("🚫 این نجوا برای شما نیست!")

    await query.message.reply_html(
        f"💌 <b>نجوا از طرف:</b> {whisper['from']}\n\n"
        f"<b>متن:</b> {whisper['text']}"
    )

# ثبت در اپ اصلی
def register_whisper_handler(application):
    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^نجوا$"), start_whisper)],
        states={
            ASK_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_message)],
            ASK_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_message)]
        },
        fallbacks=[],
    )

    application.add_handler(conv)
    application.add_handler(CallbackQueryHandler(open_whisper, pattern=r"^whisper:"))
