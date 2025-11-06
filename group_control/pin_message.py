import re
import asyncio
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from datetime import timedelta, datetime

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

    # فقط مدیران یا سودوها
    if text.startswith("پن") or text.startswith("حذف پن"):
        if not await _has_access(context, chat.id, user.id):
            return await msg.reply_text("🚫 فقط مدیران یا سودوها مجاز به این کار هستند!")

    # ========== 📌 پن (با پشتیبانی از زمان) ==========
    if text.startswith("پن"):
        if not msg.reply_to_message:
            return await msg.reply_text("⚠️ باید روی پیام مورد نظر ریپلای کنی تا سنجاق شود!")

        try:
            # استخراج مدت زمان از متن (مثل "پن 2 دقیقه" یا "پن 10 ثانیه")
            match = re.search(r"(\d+)\s*(ثانیه|دقیقه|ساعت)?", text)
            duration = 0
            if match:
                num = int(match.group(1))
                unit = match.group(2)
                if unit == "ساعت":
                    duration = num * 3600
                elif unit == "دقیقه":
                    duration = num * 60
                elif unit == "ثانیه":
                    duration = num
                else:
                    duration = 0

            # 📌 سنجاق
            await context.bot.pin_chat_message(
                chat_id=chat.id,
                message_id=msg.reply_to_message.message_id,
                disable_notification=True
            )

            # اگر زمان داده شده → بعد از اون مدت حذف بشه
            if duration > 0:
                await msg.reply_text(f"📌 پیام سنجاق شد و بعد از {num} {unit} حذف می‌شود.")
                await asyncio.sleep(duration)
                try:
                    await context.bot.unpin_chat_message(
                        chat_id=chat.id,
                        message_id=msg.reply_to_message.message_id
                    )
                    await msg.reply_text(f"⏳ پیام سنجاق‌شده پس از {num} {unit} حذف شد.")
                except:
                    pass
            else:
                await msg.reply_text("📌 پیام با موفقیت سنجاق شد (بدون زمان محدود).")

        except Exception as e:
            return await msg.reply_text(f"⚠️ خطا در سنجاق پیام: {e}")

    # ========== ❌ حذف پن ==========
    if text.startswith("حذف پن"):
        try:
            # حالت 1️⃣ : با ریپلای → حذف فقط همان پیام
            if msg.reply_to_message:
                await context.bot.unpin_chat_message(
                    chat_id=chat.id,
                    message_id=msg.reply_to_message.message_id
                )
                return await msg.reply_text("❌ پیام ریپلای‌شده از سنجاق خارج شد.")

            # حالت 2️⃣ : بدون ریپلای → حذف همه سنجاق‌ها
            else:
                await context.bot.unpin_all_chat_messages(chat.id)
                return await msg.reply_text("🧹 همه‌ی پیام‌های سنجاق‌شده حذف شدند.")

        except Exception as e:
            return await msg.reply_text(f"⚠️ خطا در حذف سنجاق: {e}")


# ================= 🔧 ثبت هندلر =================
def register_pin_handlers(application, group_number: int = 12):
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
