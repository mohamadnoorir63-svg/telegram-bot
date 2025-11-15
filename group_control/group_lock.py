from telegram import ChatPermissions, Update
from telegram.ext import CommandHandler, Application, ContextTypes

# قفل گروه
async def lock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = context.bot_data.get("lock_group_id")
    if group_id and update.effective_chat.id != group_id:
        return  # فقط گروه مشخص می‌تواند این دستور را اجرا کند

    try:
        await update.effective_chat.set_permissions(
            ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False
            )
        )
        await update.message.reply_text("🔒 گروه *قفل* شد.\nاعضا اجازه ارسال پیام ندارند.", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")


# بازکردن گروه
async def unlock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = context.bot_data.get("lock_group_id")
    if group_id and update.effective_chat.id != group_id:
        return  # فقط گروه مشخص می‌تواند این دستور را اجرا کند

    try:
        await update.effective_chat.set_permissions(
            ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        await update.message.reply_text("🔓 گروه *باز* شد.\nاعضا می‌توانند پیام ارسال کنند.", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")


# ثبت هندلرها با امکان تعیین group_id
def register_group_lock_handlers(app: Application, group: int = None):
    if group:
        app.bot_data["lock_group_id"] = group  # ذخیره گروه مشخص

    app.add_handler(CommandHandler("قفل_گروه", lock_group))
    app.add_handler(CommandHandler("بازکردن_گروه", unlock_group))
