import asyncio
from telegram import ChatPermissions, Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

# -------------------- سودو --------------------
SUPERUSER_ID = 8588347189  # آیدی سودو اصلی

# -------------------- تابع کمکی --------------------
def safe_permissions(chat):
    """بررسی و برگرداندن مجوزهای چت"""
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

# -------------------- بررسی دسترسی --------------------
async def is_admin_or_sudo(update: Update):
    user = update.effective_user
    if user.id == SUPERUSER_ID:
        return True
    member = await update.effective_chat.get_member(user.id)
    return member.status in ['administrator', 'creator']

# -------------------- قفل و باز گروه --------------------
async def lock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin_or_sudo(update):
        return
    try:
        await update.effective_chat.set_permissions(ChatPermissions(can_send_messages=False))
        # پیام قفل ثابت بمونه
        await update.message.reply_text(
            f"🔒 گروه به دستور {update.effective_user.first_name} تا اطلاع ثانوی قفل شد!\n"
            f"🛡️ تمام اعضا تا اطلاع بعدی نمی‌توانند پیام بفرستند."
        )
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {e}")

async def unlock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin_or_sudo(update):
        return
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

        # پیام باز شدن بعد 10 ثانیه حذف می‌شود
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
