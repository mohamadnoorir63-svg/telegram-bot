import asyncio
from telegram import ChatPermissions, Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

SUPERUSER_ID = 8588347189  # آیدی سودو اصلی

# -------------------- نگه داشتن پیام‌های قفل --------------------
LOCK_MESSAGES = {}      # پیام قفل یا باز گروه
TEMP_MESSAGES = {}      # پیام‌های هشدار "از قبل قفل بود / باز بود"

# -------------------- بررسی دسترسی --------------------
async def is_admin_or_sudo(update: Update):
    user = update.effective_user
    if user.id == SUPERUSER_ID:
        return True
    member = await update.effective_chat.get_member(user.id)
    return member.status in ['administrator', 'creator']

# -------------------- وضعیت گروه --------------------
def get_can_send_messages(chat):
    perms = chat.permissions
    if perms is None:
        return True  # اگر هیچ مجوزی تعریف نشده، گروه باز است
    return perms.can_send_messages

# -------------------- قفل گروه --------------------
async def lock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin_or_sudo(update):
        return
    chat = update.effective_chat

    # حذف پیام هشدار قبلی در صورت وجود
    if chat.id in TEMP_MESSAGES:
        try:
            await TEMP_MESSAGES[chat.id].delete()
        except:
            pass
        TEMP_MESSAGES.pop(chat.id)

    if not get_can_send_messages(chat):
        # گروه قبلاً قفل بود
        msg = await update.message.reply_text("⚠️ گروه از قبل قفل بود!")
        TEMP_MESSAGES[chat.id] = msg
        await asyncio.sleep(10)
        try:
            await msg.delete()
        except:
            pass
        TEMP_MESSAGES.pop(chat.id, None)
        return

    try:
        await chat.set_permissions(ChatPermissions(can_send_messages=False))

        # حذف پیام قفل قبلی
        if chat.id in LOCK_MESSAGES:
            try:
                await LOCK_MESSAGES[chat.id].delete()
            except:
                pass
            LOCK_MESSAGES.pop(chat.id)

        msg = await update.message.reply_text(
            f"🔒 گروه به دستور {update.effective_user.first_name} قفل شد!\n🛡️ تمام اعضا تا اطلاع بعدی نمی‌توانند پیام بفرستند."
        )
        LOCK_MESSAGES[chat.id] = msg
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {e}")

# -------------------- باز کردن گروه --------------------
async def unlock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin_or_sudo(update):
        return
    chat = update.effective_chat

    # حذف پیام هشدار قبلی
    if chat.id in TEMP_MESSAGES:
        try:
            await TEMP_MESSAGES[chat.id].delete()
        except:
            pass
        TEMP_MESSAGES.pop(chat.id)

    if get_can_send_messages(chat):
        # گروه قبلاً باز بود
        msg = await update.message.reply_text("⚠️ گروه از قبل باز بود!")
        TEMP_MESSAGES[chat.id] = msg
        await asyncio.sleep(10)
        try:
            await msg.delete()
        except:
            pass
        TEMP_MESSAGES.pop(chat.id, None)
        return

    try:
        perms = chat.permissions or ChatPermissions()
        new_perms = ChatPermissions(
            can_send_messages=True,
            can_send_audios=perms.can_send_audios,
            can_send_documents=perms.can_send_documents,
            can_send_photos=perms.can_send_photos,
            can_send_videos=perms.can_send_videos,
            can_send_video_notes=perms.can_send_video_notes,
            can_send_voice_notes=perms.can_send_voice_notes,
            can_send_polls=perms.can_send_polls,
            can_send_other_messages=perms.can_send_other_messages,
            can_add_web_page_previews=perms.can_add_web_page_previews,
            can_invite_users=perms.can_invite_users,
            can_pin_messages=perms.can_pin_messages,
            can_change_info=perms.can_change_info
        )
        await chat.set_permissions(new_perms)

        # حذف پیام قفل قبلی
        if chat.id in LOCK_MESSAGES:
            try:
                await LOCK_MESSAGES[chat.id].delete()
            except:
                pass
            LOCK_MESSAGES.pop(chat.id)

        msg = await update.message.reply_text(
            f"🔓 گروه به دستور {update.effective_user.first_name} باز شد!\n✅ حالا همه می‌توانند پیام بفرستند."
        )
        LOCK_MESSAGES[chat.id] = msg
        await asyncio.sleep(10)
        try:
            await msg.delete()
        except:
            pass
        LOCK_MESSAGES.pop(chat.id, None)
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {e}")

# -------------------- هندلر متن --------------------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().replace("‌", "").lower()
    if text == "قفل گروه":
        await lock_group(update, context)
    elif text == "بازکردن گروه":
        await unlock_group(update, context)

# -------------------- ثبت هندلر --------------------
def register_group_lock_handlers(app: Application, group: int = 17):
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text), group=group)
