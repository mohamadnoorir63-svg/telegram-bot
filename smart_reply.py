# ===================== 🤖 smart_reply.py =====================
from telegram import Update
from telegram.ext import ContextTypes
import random
import re
from datetime import datetime

# می‌تونی بعداً این دو تابعو وصل کنی به memory یا emotion_memory
from emotion_memory import remember_emotion, get_last_emotion


# ===================== 🧠 تابع اصلی پاسخ هوشمند =====================
async def smart_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پاسخ هوشمند خنگول — با کنترل خطا و حافظه احساسی"""

    try:
        # ===== بررسی پیام =====
        if not update.message or not update.message.text:
            return

        text = update.message.text.strip().lower()
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id

        print(f"🧠 [smart_response] دریافت شد از {user_id} در {chat_id}: {text}")

        # ===== پاسخ‌های خاص =====
        if any(word in text for word in ["سلام", "درود", "hi", "hello"]):
            await update.message.reply_text(random.choice([
                "سلام رفیق 🌞",
                "درود بر تو ✋",
                "سلام! حالت چطوره؟ 😄",
                "سلام به روی ماهت 🌹"
            ]))
            await remember_emotion(user_id, "happy")
            return

        elif any(word in text for word in ["خداحافظ", "بای", "bye"]):
            await update.message.reply_text(random.choice([
                "خدانگهدار 🌙",
                "فعلاً 👋",
                "مواظب خودت باش 💫"
            ]))
            await remember_emotion(user_id, "neutral")
            return

        # ===== پاسخ به حالت احساسی =====
        if "😢" in text or "غمگین" in text:
            await update.message.reply_text("ناراحت نباش، من اینجام 🤗")
            await remember_emotion(user_id, "sad")
            return

        if "😂" in text or "خنده" in text:
            await update.message.reply_text("خوشحالم که خندیدی 😄")
            await remember_emotion(user_id, "happy")
            return

        # ===== پاسخ عمومی =====
        if re.search(r"چطوری|حالت چطوره|چه خبر", text):
            mood = await get_last_emotion(user_id)
            if mood == "happy":
                await update.message.reply_text("خوبه، تو هم که خوشحالی 😄")
            elif mood == "sad":
                await update.message.reply_text("یکم گرفته‌ام، ولی تو که بیای بهتر می‌شه 💫")
            else:
                await update.message.reply_text("بد نیستم، مرسی که پرسیدی 🫶")
            return

        # ===== پاسخ هوش مصنوعی ساده =====
        responses = [
            "جالبه 😄",
            "می‌تونی بیشتر بگی؟ 🤔",
            "آهااا فهمیدم 👀",
            "خب بعدش چی شد؟ 😅",
            "عه جدی؟ 😳"
        ]
        await update.message.reply_text(random.choice(responses))
        await remember_emotion(user_id, "neutral")

    except Exception as e:
        print(f"❌ [smart_response ERROR]: {e}")
        await update.message.reply_text("⚠️ خطای موقتی در پاسخ‌دهی. لطفاً دوباره تلاش کن.")
