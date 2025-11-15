from telegram import ChatPermissions, Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

def safe_permissions(chat):
    """اگر chat.permissions مقدار نداشت، مقدار پیش‌فرض بساز"""
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

# -------------------- قفل --------------------
async def lock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.effective_chat.set_permissions(ChatPermissions(can_send_messages=False))
        await update.message.reply_text(
            "🔒 گروه به دستور {} تا اطلاع ثانوی قفل شد!\nلطفاً صبور باشید، همه پیام‌ها موقتاً مسدود شده‌اند.".format(update.effective_user.first_name)
        )
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")

# -------------------- باز --------------------
async def unlock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat = update.effective_chat
        current = safe_permissions(chat)
        new_permissions = ChatPermissions(
            can_send_messages=True,
            can_send_audios=current.can_send_audios,
            can_send_documents=current.can_send_documents,
            can_send_photos=current.can_send_photos,
            can_send_videos=current.can_send_videos,
            can_send_video_notes=current.can_send_video_notes,
            can_send_voice_notes=current.can_send_voice_notes,
            can_send_polls=current.can_send_polls,
            can_send_other_messages=current.can_send_other_messages,
            can_add_web_page_previews=current.can_add_web_page_previews,
            can_invite_users=current.can_invite_users,
            can_pin_messages=current.can_pin_messages,
            can_change_info=current.can_change_info
        )
        await chat.set_permissions(new_permissions)
        await update.message.reply_text(
            "🔓 گروه به دستور {} باز شد!\nحالا همه می‌توانند پیام بفرستند.".format(update.effective_user.first_name),
            delete_after=10  # بعد از ۱۰ ثانیه حذف می‌شود
        )
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")

# -------------------- هندلر --------------------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().replace("‌", "").lower()
    if text == "قفل گروه":
        await lock_group(update, context)
    elif text == "باز کردن گروه":
        await unlock_group(update, context)

def register_group_lock_handlers(app: Application, group: int = 17):
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text), group=group)
