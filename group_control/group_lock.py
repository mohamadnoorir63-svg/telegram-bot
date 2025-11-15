import asyncio
from telegram import ChatPermissions, Update
from telegram.ext import MessageHandler, filters, ContextTypes


def safe_permissions(chat):
    """
    اگر chat.permissions خالی بود، یک نسخه پیش‌فرض با تمام True برمی‌گرداند.
    """
    p = chat.permissions
    if p is None:
        return ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_send_photos=True,
            can_send_videos=True,
            can_send_voice_notes=True,
            can_send_video_notes=True,
            can_send_documents=True,
            can_send_audios=True,
        )
    return p


# ─────────────────────────────── قفل ───────────────────────────────
async def lock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    member = await context.bot.get_chat_member(chat.id, user.id)
    if member.status not in ("administrator", "creator"):
        return await update.message.reply_text("🚫 فقط مدیران می‌توانند گروه را قفل کنند.")

    current = safe_permissions(chat)

    # جلوگیری از قفل دوباره
    if current.can_send_messages is False:
        msg = await update.message.reply_text("🔒 گروه از قبل قفل است.")
        await asyncio.sleep(3)
        return await msg.delete()

    new_perms = ChatPermissions(
        can_send_messages=False,

        can_send_media_messages=current.can_send_media_messages,
        can_send_other_messages=current.can_send_other_messages,
        can_add_web_page_previews=current.can_add_web_page_previews,
        can_send_photos=current.can_send_photos,
        can_send_videos=current.can_send_videos,
        can_send_voice_notes=current.can_send_voice_notes,
        can_send_video_notes=current.can_send_video_notes,
        can_send_documents=current.can_send_documents,
        can_send_audios=current.can_send_audios,
    )

    await context.bot.set_chat_permissions(chat.id, new_perms)

    msg = await update.message.reply_text("🔒 گروه قفل شد.")
    await asyncio.sleep(4)
    await msg.delete()
    await update.message.delete()


# ─────────────────────────────── باز کردن ───────────────────────────────
async def unlock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    member = await context.bot.get_chat_member(chat.id, user.id)
    if member.status not in ("administrator", "creator"):
        return await update.message.reply_text("🚫 فقط مدیران می‌توانند گروه را باز کنند.")

    current = safe_permissions(chat)

    # جلوگیری از باز کردن تکراری
    if current.can_send_messages is True:
        msg = await update.message.reply_text("🔓 گروه از قبل باز است.")
        await asyncio.sleep(3)
        return await msg.delete()

    new_perms = ChatPermissions(
        can_send_messages=True,

        can_send_media_messages=current.can_send_media_messages,
        can_send_other_messages=current.can_send_other_messages,
        can_add_web_page_previews=current.can_add_web_page_previews,
        can_send_photos=current.can_send_photos,
        can_send_videos=current.can_send_videos,
        can_send_voice_notes=current.can_send_voice_notes,
        can_send_video_notes=current.can_send_video_notes,
        can_send_documents=current.can_send_documents,
        can_send_audios=current.can_send_audios,
    )

    await context.bot.set_chat_permissions(chat.id, new_perms)

    msg = await update.message.reply_text("🔓 گروه باز شد.")
    await asyncio.sleep(4)
    await msg.delete()
    await update.message.delete()


# ─────────────────────────────── روتر ───────────────────────────────
async def group_lock_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    if text == "قفل گروه":
        return await lock_group(update, context)

    if text in ("باز کردن گروه", "بازکردن گروه", "باز کردن چت"):
        return await unlock_group(update, context)


# ─────────────────────────────── ثبت هندلر ───────────────────────────────
def register_group_lock_handlers(application, group=-10):
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, group_lock_router),
        group=group
    )

    print(f"✅ هندلرهای قفل گروه ثبت شدند (group={group})")
