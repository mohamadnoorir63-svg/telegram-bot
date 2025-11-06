import os, json
from telegram import Update, ChatPermissions
from telegram.ext import CommandHandler, ContextTypes

# 📁 فایل ذخیره اخطارها
WARN_FILE = "warnings.json"

def load_warnings():
    if os.path.exists(WARN_FILE):
        try:
            with open(WARN_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_warnings(data):
    with open(WARN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 🚫 بن
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return await update.message.reply_text("⚠️ باید روی پیام فرد ریپلای کنی تا بن بشه!")

    target = update.message.reply_to_message.from_user
    chat = update.effective_chat
    member = await context.bot.get_chat_member(chat.id, update.effective_user.id)

    if member.status not in ["administrator", "creator"]:
        return await update.message.reply_text("⛔ فقط مدیران مجازند!")

    try:
        await context.bot.ban_chat_member(chat.id, target.id)
        await update.message.reply_text(f"🚫 {target.first_name} از گروه بن شد!")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در بن: {e}")

# 🤐 سکوت
async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return await update.message.reply_text("⚠️ باید روی پیام فرد ریپلای کنی تا سکوتش کنم!")

    target = update.message.reply_to_message.from_user
    chat = update.effective_chat
    member = await context.bot.get_chat_member(chat.id, update.effective_user.id)

    if member.status not in ["administrator", "creator"]:
        return await update.message.reply_text("⛔ فقط مدیران مجازند!")

    try:
        await context.bot.restrict_chat_member(
            chat.id,
            target.id,
            permissions=ChatPermissions(can_send_messages=False)
        )
        await update.message.reply_text(f"🤐 {target.first_name} در سکوت قرار گرفت!")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در سکوت: {e}")

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return await update.message.reply_text("⚠️ باید روی پیام فرد ریپلای کنی تا از سکوت دربیاد!")

    target = update.message.reply_to_message.from_user
    chat = update.effective_chat
    member = await context.bot.get_chat_member(chat.id, update.effective_user.id)

    if member.status not in ["administrator", "creator"]:
        return await update.message.reply_text("⛔ فقط مدیران مجازند!")

    try:
        await context.bot.restrict_chat_member(
            chat.id,
            target.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True
            )
        )
        await update.message.reply_text(f"🔊 {target.first_name} از سکوت خارج شد.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در unmute: {e}")

# ⚠️ اخطارها
async def warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return await update.message.reply_text("⚠️ باید روی پیام فرد ریپلای کنی تا اخطار بگیره!")

    target = update.message.reply_to_message.from_user
    chat = update.effective_chat
    member = await context.bot.get_chat_member(chat.id, update.effective_user.id)
    if member.status not in ["administrator", "creator"]:
        return await update.message.reply_text("⛔ فقط مدیران مجازند!")

    data = load_warnings()
    key = f"{chat.id}:{target.id}"
    data[key] = data.get(key, 0) + 1
    save_warnings(data)

    count = data[key]
    if count >= 3:
        try:
            await context.bot.ban_chat_member(chat.id, target.id)
            await update.message.reply_text(f"🚫 {target.first_name} به‌دلیل ۳ اخطار بن شد!")
        except:
            await update.message.reply_text("⚠️ نتونستم بن کنم ولی اخطار سوم ثبت شد.")
    else:
        await update.message.reply_text(f"⚠️ {target.first_name} اخطار {count}/3 گرفت.")

async def reset_warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return await update.message.reply_text("⚠️ باید روی پیام کاربر ریپلای کنی!")

    target = update.message.reply_to_message.from_user
    chat = update.effective_chat
    data = load_warnings()
    key = f"{chat.id}:{target.id}"

    if key in data:
        del data[key]
        save_warnings(data)
        await update.message.reply_text(f"✅ اخطارهای {target.first_name} پاک شد.")
    else:
        await update.message.reply_text("ℹ️ این کاربر اخطاری نداشت.")

# ⚙️ ثبت هندلرها
def register_punishment_handlers(application, group_number: int = 10):
    """ثبت هندلرها با شماره گروه دلخواه (پیش‌فرض group=10)"""
    application.add_handler(CommandHandler("ban", ban_user), group=group_number)
    application.add_handler(CommandHandler("mute", mute_user), group=group_number)
    application.add_handler(CommandHandler("unmute", unmute_user), group=group_number)
    application.add_handler(CommandHandler("warn", warn_user), group=group_number)
    application.add_handler(CommandHandler("resetwarn", reset_warn), group=group_number)
