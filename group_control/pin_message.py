# ================= ⚙️ کنترل سنجاق و حذف سنجاق پیام‌ها =================
import re
import asyncio
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

# آیدی سودوها (می‌تونی آیدی خودت و بقیه مدیرهای اصلی رو بزاری)
SUDO_IDS = [8588347189]


# ================= 🔐 بررسی دسترسی =================
async def _has_access(context, chat_id: int, user_id: int) -> bool:
    """بررسی اینکه آیا کاربر مجاز به سنجاق هست یا نه"""
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except:
        return False


# ================= 📌 سنجاق و ❌ حذف سنجاق =================
async def handle_pin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    text = (msg.text or "").strip()

    # فقط در گروه‌ها
    if chat.type not in ("group", "supergroup"):
        return

    # ✅ فقط اگر واقعاً دستور "پن" باشه، نه "پنل"
    if re.match(r"^پن($|\s)", text) or text.startswith("حذف پن"):

        # بررسی سطح دسترسی
        if not await _has_access(context, chat.id, user.id):
            return await msg.reply_text("🚫 فقط مدیران یا سودوها مجاز به این کار هستند!")

        # ========== 📌 پن ==========
        if re.match(r"^پن($|\s)", text):
            if not msg.reply_to_message:
                return await msg.reply_text("⚠️ باید روی پیام مورد نظر ریپلای کنی تا سنجاق شود!")

            try:
                # استخراج مدت زمان از متن (مثل «پن 2 دقیقه»)
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

                # سنجاق پیام
                await context.bot.pin_chat_message(
                    chat_id=chat.id,
                    message_id=msg.reply_to_message.message_id,
                    disable_notification=True
                )

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
                if msg.reply_to_message:
                    # حذف فقط پیام ریپلای‌شده
                    await context.bot.unpin_chat_message(
                        chat_id=chat.id,
                        message_id=msg.reply_to_message.message_id
                    )
                    return await msg.reply_text("❌ پیام ریپلای‌شده از سنجاق خارج شد.")
                else:
                    # حذف همه سنجاق‌ها
                    await context.bot.unpin_all_chat_messages(chat.id)
                    return await msg.reply_text("🧹 همه‌ی پیام‌های سنجاق‌شده حذف شدند.")
            except Exception as e:
                return await msg.reply_text(f"⚠️ خطا در حذف سنجاق: {e}")


# ================= 🔧 ثبت هندلر =================
def register_pin_handlers(application, group_number: int = 12):
    """ثبت هندلر برای دستورات پن و حذف پن"""
    application.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND
            & filters.ChatType.GROUPS,
            handle_pin_actions,
        ),
        group=group_number,
    )
