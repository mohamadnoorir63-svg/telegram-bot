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

    # فقط مدیران یا سودوها مجاز
    if text.startswith("پن") or text.startswith("حذف پن"):
        if not await _has_access(context, chat.id, user.id):
            return await msg.reply_text("🚫 فقط مدیران یا سودوها مجاز به این کار هستند!")

    # ========== 📌 پن ==========
    if text.startswith("پن"):
        # بررسی زمان در دستور (مثلاً "پن 2 دقیقه")
        match = re.search(r"(\d+)\s*(ثانیه|دقیقه|ساعت)?", text)
        duration = 0
        num = 0
        unit = None

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

        # تلاش برای یافتن پیام هدف
        target_message = None

        # حالت ۱️⃣: ریپلای شده
        if msg.reply_to_message:
            target_message = msg.reply_to_message

        # حالت ۲️⃣: بدون ریپلای ولی از پنل (ربات خودش ارسال کرده)
        elif msg.from_user.id == context.bot.id:
            # پیدا کردن آخرین پیام واقعی در گروه (غیر از پیام ربات)
            async for message in context.bot.get_chat_history(chat.id, limit=20):
                if message.from_user and message.from_user.id != context.bot.id:
                    target_message = message
                    break

        # اگر پیامی برای سنجاق یافت نشد:
        if not target_message:
            return await msg.reply_text("⚠️ باید روی پیام مورد نظر ریپلای کنی تا سنجاق شود!")

        try:
            # 📌 سنجاق
            await context.bot.pin_chat_message(
                chat_id=chat.id,
                message_id=target_message.message_id,
                disable_notification=True
            )

            # اگر زمان داده شده → بعد از اون مدت حذف بشه
            if duration > 0:
                await msg.reply_text(f"📌 پیام سنجاق شد و بعد از {num} {unit} حذف می‌شود.")
                await asyncio.sleep(duration)
                try:
                    await context.bot.unpin_chat_message(
                        chat_id=chat.id,
                        message_id=target_message.message_id
                    )
                    await msg.reply_text(f"⏳ پیام سنجاق‌شده پس از {num} {unit} حذف شد.")
                except:
                    pass
            else:
                await msg.reply_text("📌 پیام با موفقیت سنجاق شد (بدون زمان محدود).")

        except Exception as e:
            return await msg.reply_text(f"⚠️ خطا در سنجاق پیام:\n{e}")

    # ========== ❌ حذف پن ==========
    if text.startswith("حذف پن"):
        try:
            if msg.reply_to_message:
                # حالت ۱️⃣: ریپلای → حذف فقط همان پیام
                await context.bot.unpin_chat_message(
                    chat_id=chat.id,
                    message_id=msg.reply_to_message.message_id
                )
                return await msg.reply_text("❌ پیام ریپلای‌شده از سنجاق خارج شد.")
            else:
                # حالت ۲️⃣: بدون ریپلای → حذف همه سنجاق‌ها
                await context.bot.unpin_all_chat_messages(chat.id)
                return await msg.reply_text("🧹 همه‌ی پیام‌های سنجاق‌شده حذف شدند.")
        except Exception as e:
            return await msg.reply_text(f"⚠️ خطا در حذف سنجاق:\n{e}")


# ================= 🔧 ثبت هندلر =================
def register_pin_handlers(application, group_number: int = 12):
    """ثبت هندلر سنجاق و حذف سنجاق"""
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
            handle_pin_actions,
        ),
        group=group_number,
    )
