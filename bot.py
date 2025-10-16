# ======================= 💫 خنگول فارسی Ultra Final Cloud+ v9.9 =======================
from telegram import ChatPermissions, Update, InputFile
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
import asyncio, os, json, math

# ===== تنظیمات =====
ADMIN_ID = 123456789  # آیدی عددی ادمین اصلی
CLEAN_DONE_PHOTO = "clean_done.jpg"  # عکس نهایی پاکسازی (در پوشه ربات بذار)

WARN_FILE = "warnings.json"

# ===== اخطار =====
def load_warnings():
    if os.path.exists(WARN_FILE):
        with open(WARN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_warnings(data):
    with open(WARN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

warnings = load_warnings()

# ===== چک ادمین =====
async def is_admin(update, context, user_id=None):
    if user_id is None:
        user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        return True
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
        return member.status in ["administrator", "creator"]
    except:
        return False

# ===== alias mapping =====
ALIASES = {
    "بن": "/ban",
    "از_بن_درآر": "/unban",
    "سکوت": "/mute",
    "آزاد": "/unmute",
    "اخطار": "/warn",
    "پاک_اخطار": "/unwarn",
    "پاکسازی": "/purge",
    "پاکسازی_کل": "/purgeall",
    "پاکسازی_کل_گروه": "/purgeall"
}

async def alias_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    parts = text.split()
    cmd = parts[0]
    if cmd in ALIASES:
        new_text = ALIASES[cmd] + (" " + " ".join(parts[1:]) if len(parts) > 1 else "")
        update.message.text = new_text
        await app.process_update(update)
        return True
    return False

# ======================= 🚫 بن =======================
async def cmd_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text("⛔ فقط مدیران می‌تونن بن کنن!")
    if not update.message.reply_to_message:
        return await update.message.reply_text("⚙️ روی پیام کاربر ریپلای کن تا بن بشه.")
    user = update.message.reply_to_message.from_user
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, user.id)
        await update.message.reply_text(f"🚫 {user.first_name} از گروه بن شد 😈")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در بن: {e}")

# ======================= 🔊 حذف بن =======================
async def cmd_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        return await update.message.reply_text("⚙️ روی پیام کاربر ریپلای کن تا از بن خارج شه.")
    user = update.message.reply_to_message.from_user
    try:
        await context.bot.unban_chat_member(update.effective_chat.id, user.id)
        await update.message.reply_text(f"✅ {user.first_name} از بن آزاد شد 🕊")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در حذف بن: {e}")

# ======================= 🔇 سکوت =======================
async def cmd_mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        return await update.message.reply_text("⚙️ روی پیام کاربر ریپلای کن تا بی‌صدا بشه.")
    user = update.message.reply_to_message.from_user
    try:
        perms = ChatPermissions(can_send_messages=False)
        await context.bot.restrict_chat_member(update.effective_chat.id, user.id, perms)
        await update.message.reply_text(f"🔇 {user.first_name} ساکت شد 😶")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در سکوت: {e}")

# ======================= 🔊 حذف سکوت =======================
async def cmd_unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        return await update.message.reply_text("⚙️ روی پیام کاربر ریپلای کن تا آزاد شه.")
    user = update.message.reply_to_message.from_user
    try:
        perms = ChatPermissions(can_send_messages=True)
        await context.bot.restrict_chat_member(update.effective_chat.id, user.id, perms)
        await update.message.reply_text(f"🔊 {user.first_name} از سکوت دراومد 😄")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در حذف سکوت: {e}")

# ======================= ⚠️ اخطار =======================
async def cmd_warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        return await update.message.reply_text("⚙️ روی پیام کاربر ریپلای کن تا اخطار بگیره.")
    user = update.message.reply_to_message.from_user
    chat_id = str(update.effective_chat.id)
    user_id = str(user.id)
    warnings.setdefault(chat_id, {})
    warnings[chat_id][user_id] = warnings[chat_id].get(user_id, 0) + 1
    save_warnings(warnings)
    count = warnings[chat_id][user_id]
    msg = f"⚠️ {user.first_name} اخطار گرفت.\n📊 اخطار فعلی: {count}/3"
    if count >= 3:
        try:
            await context.bot.ban_chat_member(update.effective_chat.id, user.id)
            msg += "\n🚫 به ۳ اخطار رسید → بن شد!"
        except:
            msg += "\n⚠️ نتونستم بنش کنم!"
    await update.message.reply_text(msg)

# ======================= 🧹 حذف اخطار =======================
async def cmd_unwarn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        return await update.message.reply_text("⚙️ روی پیام کاربر ریپلای کن تا یک اخطارش حذف شه.")
    user = update.message.reply_to_message.from_user
    chat_id = str(update.effective_chat.id)
    user_id = str(user.id)
    if chat_id in warnings and user_id in warnings[chat_id]:
        warnings[chat_id][user_id] = max(0, warnings[chat_id][user_id] - 1)
        save_warnings(warnings)
        await update.message.reply_text(f"✅ یک اخطار از {user.first_name} حذف شد.")
    else:
        await update.message.reply_text("ℹ️ این کاربر اخطاری نداشت.")

# ======================= 💣 پاکسازی کل گروه با پیام نهایی =======================
async def cmd_purge_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text("⛔ فقط مدیران مجازند!")

    msg = await update.message.reply_text("💣 در حال پاکسازی کل گروه... لطفاً منتظر بمانید ⏳")

    chat_id = update.effective_chat.id
    last_id = update.message.message_id
    total_deleted = 0
    step = 10000

    while last_id > 1:
        ids = list(range(last_id, max(1, last_id - step), -1))
        tasks = [asyncio.create_task(context.bot.delete_message(chat_id, i)) for i in ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_deleted += sum(1 for r in results if r is None)
        last_id -= step

        await msg.edit_text(
            f"🧹 در حال پاکسازی...\n✅ حذف‌شده: {total_deleted:,}\n📉 ادامه دارد..."
        )
        await asyncio.sleep(3)

        if last_id <= 1:
            break

    await msg.delete()

    caption = (
        f"✨ <b>پاکسازی کامل شد!</b>\n\n"
        f"🧹 تمام پیام‌های گروه با موفقیت حذف شدند.\n"
        f"👑 مدیریت: <a href='tg://user?id={update.effective_user.id}'>{update.effective_user.first_name}</a>\n"
        f"🤖 <b>ساخته‌شده با خنگول فارسی</b>"
    )

    # اگر عکس وجود داشت با عکس بفرست
    if os.path.exists(CLEAN_DONE_PHOTO):
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=InputFile(CLEAN_DONE_PHOTO),
            caption=caption,
            parse_mode="HTML"
        )
    else:
        await context.bot.send_message(chat_id=chat_id, text=caption, parse_mode="HTML")
