import json
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, CallbackQueryHandler, ApplicationBuilder, filters
from cryptography.fernet import Fernet
import re

# مسیر ذخیره نجواها و کلید رمزگذاری
WHISPER_FILE = "whispers.json"
KEY_FILE = "whisper_key.key"

# ساخت کلید رمزگذاری اگر وجود نداشت
if not os.path.exists(KEY_FILE):
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(key)
else:
    with open(KEY_FILE, "rb") as f:
        key = f.read()

fernet = Fernet(key)

# ساخت فایل نجوا اگر وجود نداشت
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

async def whisper_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش پیام PV بدون /"""
    message_text = update.message.text

    # بررسی فرمت: Najwa @username متن
    match = re.match(r'^Najwa\s+@?([A-Za-z0-9_]+)\s+(.+)', message_text)
    if not match:
        return  # نادیده گرفتن پیام‌هایی که با Najwa شروع نمی‌شوند

    target_username = match.group(1)
    text = match.group(2)
    sender = update.effective_user
    chat_id = update.effective_chat.id

    # حذف پیام فرستنده تا در گروه دیده نشود
    await update.message.delete()

    # پیدا کردن کاربر هدف
    target_user = None
    try:
        members = await context.bot.get_chat_administrators(chat_id)
        for m in members:
            if m.user.username and m.user.username.lower() == target_username.lower():
                target_user = m.user
                break
    except:
        pass

    if not target_user:
        # اگر کاربر پیدا نشد، می‌توان اعلان داد (اختیاری)
        return

    # رمزگذاری متن
    encrypted_text = fernet.encrypt(text.encode()).decode()

    # ذخیره نجوا
    whispers = load_whispers()
    whisper_id = f"{chat_id}_{sender.id}_{target_user.id}_{len(whispers)+1}"
    whispers[whisper_id] = {
        "from_id": sender.id,
        "from_name": sender.first_name,
        "to_id": target_user.id,
        "to_name": target_user.first_name,
        "text": encrypted_text,
        "chat": chat_id
    }
    save_whispers(whispers)

    # ارسال اعلان عمومی با دکمه
    button = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton(f"📩 مشاهده نجوا برای {target_user.first_name}", callback_data=f"whisper:{whisper_id}")
    )
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"🤫 {target_user.first_name} شما یک نجوا از طرف {sender.first_name} دارید!",
        reply_markup=button
    )

    # حذف خودکار بعد ۵ دقیقه
    async def auto_delete():
        await asyncio.sleep(300)
        data = load_whispers()
        if whisper_id in data:
            del data[whisper_id]
            save_whispers(data)

    asyncio.create_task(auto_delete())

async def open_whisper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """باز کردن نجوا فقط برای گیرنده"""
    query = update.callback_query
    await query.answer()
    whisper_id = query.data.split(":")[1]
    whispers = load_whispers()
    whisper = whispers.get(whisper_id)

    if not whisper:
        return await query.message.reply_text("⚠️ این نجوا منقضی شده یا حذف شده.")

    if query.from_user.id != whisper["to_id"]:
        return await query.message.reply_text("🚫 این نجوا برای شما نیست!")

    decrypted_text = fernet.decrypt(whisper["text"].encode()).decode()

    await query.message.reply_html(
        f"💌 <b>نجوا از طرف:</b> {whisper['from_name']}\n\n"
        f"<b>متن:</b> {decrypted_text}"
    )

def register_whisper_handler(application):
    # پیام‌هایی که با "Najwa " شروع می‌شوند
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, whisper_message))
    # دکمه باز کردن نجوا
    application.add_handler(CallbackQueryHandler(open_whisper, pattern=r"^whisper:"))
