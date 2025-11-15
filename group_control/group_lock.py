from telegram import ChatPermissions, Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters


# --------------------- قفل گروه ---------------------
async def lock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat = update.effective_chat

        # گرفتن مجوزهای فعلی
        current = chat.permissions

        # ساختن نسخه‌ی جدید با حفظ همه‌ی گزینه‌ها
        new_permissions = ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=current.can_send_media_messages,
            can_send_other_messages=current.can_send_other_messages,
            can_add_web_page_previews=current.can_add_web_page_previews,
            can_invite_users=current.can_invite_users,
            can_pin_messages=current.can_pin_messages,
            can_change_info=current.can_change_info
        )

        await chat.set_permissions(new_permissions)

        await update.message.reply_text("🔒 گروه قفل شد.")

    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")


# --------------------- باز کردن گروه ---------------------
async def unlock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat = update.effective_chat

        # گرفتن مجوزهای فعلی
        current = chat.permissions

        # بازگرداندن فقط ارسال پیام
        new_permissions = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=current.can_send_media_messages,
            can_send_other_messages=current.can_send_other_messages,
            can_add_web_page_previews=current.can_add_web_page_previews,
            can_invite_users=current.can_invite_users,
            can_pin_messages=current.can_pin_messages,
            can_change_info=current.can_change_info
        )

        await chat.set_permissions(new_permissions)

        await update.message.reply_text("🔓 گروه باز شد.")

    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")


# --------------------- هندلر ---------------------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().replace("‌", "").lower()

    if text == "قفل گروه":
        await lock_group(update, context)
    elif text == "باز کردن گروه":
        await unlock_group(update, context)


def register_group_lock_handlers(app: Application, group: int = 17):
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text), group=group)
