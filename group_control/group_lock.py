import asyncio
from telegram import ChatPermissions, Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

# -------------------- سودو --------------------
SUPERUSER_ID = 8588347189  # آیدی سودو اصلی

# -------------------- تابع کمکی --------------------
def safe_permissions(chat):
    p = chat.permissions
    if p is None:
        return ChatPermissions(
            can_send_messages=True,
            can_send_audios=True,
            can_send_documents=True,
            can_send_photos=True,
            can_send_videos=True,
            can_send_video_notes=True,
            can_send_voice_notes=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_invite_users=True,
            can_pin_messages=False,
            can_change_info=False
        )
    return p

async def is_admin_or_sudo(update: Update):
    user = update.effective_user
    if user.id == SUPERUSER_ID:
        return True
    member = await update.effective_chat.get_member(user.id)
    return member.status in ['administrator', 'creator']

# -------------------- قفل و باز گروه --------------------
LOCK_MESSAGES = {}

async def lock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin_or_sudo(update):
        return
    chat = update.effective_chat
    current_permissions = safe_permissions(chat)

    # بررسی وضعیت فعلی
    if current_permissions.can_send_messages is False:
        await update.message.reply_text("⚠️ گروه قبلاً قفل شده است!")
        return

    try:
        await chat.set_permissions(ChatPermissions(can_send_messages=False))
        msg = await update.message.reply_text(
            f"🔒 گروه به دستور {update.effective_user.first_name} تا اطلاع ثانوی قفل شد!\n"
            f"🛡️ تمام اعضا تا اطلاع بعدی نمی‌توانند پیام بفرستند."
        )
        LOCK_MESSAGES[chat.id] = msg
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {e}")

async def unlock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin_or_sudo(update):
        return
    chat = update.effective_chat
    current_permissions = safe_permissions(chat)

    # بررسی وضعیت فعلی
    if current_permissions.can_send_messages is True:
        await update.message.reply_text("⚠️ گروه قبلاً باز است!")
        return

    try:
        new_permissions = ChatPermissions(
            can_send_messages=True,
            can_send_audios=current_permissions.can_send_audios,
            can_send_documents=current_permissions.can_send_documents,
            can_send_photos=current_permissions.can_send_photos,
            can_send_videos=current_permissions.can_send_videos,
            can_send_video_notes=current_permissions.can_send_video_notes,
            can_send_voice_notes=current_permissions.can_send_voice_notes,
            can_send_polls=current_permissions.can_send_polls,
            can_send_other_messages=current_permissions.can_send_other_messages,
            can_add_web_page_previews=current_permissions.can_add_web_page_previews,
            can_invite_users=current_permissions.can_invite_users,
            can_pin_messages=current_permissions.can_pin_messages,
            can_change_info=current_permissions.can_change_info
        )
        await chat.set_permissions(new_permissions)

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
        await asyncio.sleep(10)
        await msg.delete()
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
