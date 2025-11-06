import os
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

# ================= ⚙️ تنظیمات اولیه =================
SUDO_IDS = [8588347189]  # آیدی سودوها (خودت + هرکس خواستی)


# ================= 🔐 بررسی ادمین / سودو =================
async def _has_access(context, chat_id: int, user_id: int) -> bool:
    """بررسی دسترسی کاربر برای سنجاق یا حذف سنجاق"""
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except:
        return False


# ================= 📌 سنجاق / ❌ حذف سنجاق =================
async def handle_pin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    text = (msg.text or "").strip()

    if chat.type not in ("group", "supergroup"):
        return

    # فقط روی پیام ریپلای انجام می‌شن
    if text in ["پن", "حذف پن"] and not msg.reply_to_message:
        return await msg.reply_text("⚠️ باید روی پیام مورد نظر ریپلای کنی!")

    # بررسی مجوز کاربر
    if text in ["پن", "حذف پن"]:
        if not await _has_access(context, chat.id, user.id):
            return await msg.reply_text("🚫 فقط مدیران یا سودوها مجاز به این کار هستند!")

    # ========== 📌 پن ==========
    if text == "پن":
        try:
            await context.bot.pin_chat_message(
                chat_id=chat.id,
                message_id=msg.reply_to_message.message_id,
                disable_notification=True  # بدون نوتیف برای اعضا
            )
            return await msg.reply_text("📌 پیام با موفقیت سنجاق شد.")
        except Exception as e:
            return await msg.reply_text(f"⚠️ خطا در سنجاق پیام: {e}")

    # ========== ❌ حذف پن ==========
    if text == "حذف پن":
        try:
            await context.bot.unpin_chat_message(chat.id)
            return await msg.reply_text("❌ پیام سنجاق‌شده حذف شد.")
        except Exception as e:
            return await msg.reply_text(f"⚠️ خطا در حذف سنجاق: {e}")


# ================= 🔧 ثبت هندلر =================
def register_pin_handlers(application, group_number: int = 11):
    """ثبت هندلر سنجاق و حذف سنجاق"""
    application.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND
            & filters.ChatType.GROUPS,
            handle_pin_actions,
        ),
        group=group_number,
    )
