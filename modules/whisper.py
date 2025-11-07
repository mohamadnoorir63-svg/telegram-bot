import json
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, ApplicationBuilder
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

async def whisper_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /نجوا @username متن"""
    message_text = update.message.text

    # بررسی فرمت: /نجوا @username متن
    match = re.match(r'^/نجوا\s+@?(\w+)\s+(.+)', message_text)
    if not match:
        await update.message.reply_text("❌ فرمت درست: /نجوا @username متن")
        return

    target_username = match.group(1)
    text = match.group(2)
    sender = update.effective_user
    chat_id = update.effective_chat.id

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
        await update.message.reply_text("⚠️ کاربر مورد نظر در گروه پیدا نشد.")
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
    await update.message.reply_html(
        f"🤫 <b>{target_user.first_name}</b> شما یک نجوا از طرف <b>{sender.first_name}</b> دارید!",
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
    application.add_handler(CommandHandler("نجوا", whisper_command))
    application.add_handler(CallbackQueryHandler(open_whisper, pattern=r"^whisper:"))
