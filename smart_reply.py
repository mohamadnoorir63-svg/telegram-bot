# ===================== 🤖 smart_reply.py =====================
import random
import re
from telegram import Update
from telegram.ext import ContextTypes

from memory_manager import get_reply, enhance_sentence, shadow_learn
from emotion_memory import remember_emotion, get_last_emotion, emotion_context_reply


# ===============================================================
# 😄 تشخیص احساس — Emotion Engine
# ===============================================================
def detect_emotion(text: str) -> str:
    if not text:
        return "neutral"

    text = text.lower()

    emotions = {
        "happy": ["😂", "🤣", "😅", "خوشحالم", "عالیه", "دمت گرم", "خوبه", "مرسی", "❤️"],
        "sad": ["😔", "😢", "غمگینم", "بدم میاد", "دلم گرفته", "افسرده"],
        "angry": ["😡", "لعنتی", "حرصم", "عصبانی", "بدبخت", "خفه شو"],
        "love": ["دوستت دارم", "❤️", "😘", "عاشقتم", "عشق", "قلبم"],
        "question": ["?", "چرا", "چیه", "چی شد", "کجایی", "کجا", "چطوری"],
    }

    for emo, words in emotions.items():
        for w in words:
            if w in text:
                return emo

    return "neutral"


# ===============================================================
# 💬 پاسخ هوشمند احساسی (نسخه‌ی Async برای تلگرام)
# ===============================================================
async def smart_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پاسخ پویا و احساسی در چت (هماهنگ با Telegram API)"""

    try:
        if not update.message or not update.message.text:
            return

        text = update.message.text.strip()
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id

        # تشخیص احساس فعلی
        emotion = detect_emotion(text)
        last_emotion = get_last_emotion(user_id)
        context_reply = emotion_context_reply(emotion, last_emotion)

        # اگه پاسخ زمینه‌ای هست، همونو بفرست
        if context_reply:
            await remember_emotion(user_id, emotion)
            return await update.message.reply_text(enhance_sentence(context_reply))

        # به‌روزرسانی احساس کاربر
        await remember_emotion(user_id, emotion)

        # بررسی حافظه برای پاسخ مشابه
        mem_reply = get_reply(text)
        if mem_reply:
            shadow_learn(text, mem_reply)
            return await update.message.reply_text(enhance_sentence(mem_reply))

        # پاسخ احساسی عمومی
        responses = {
            "happy": [
                "😂 خوشحالم حالت خوبه!",
                "😄 بخند که دنیا بخنده!",
                "😁 چه حس خوبی!",
            ],
            "sad": [
                "😢 نگران نباش، درست میشه.",
                "💔 بعد شب تاریک، صبح روشن میاد.",
                "😔 دلم برات یه چای داغ می‌خواد.",
            ],
            "angry": [
                "😤 آروم باش رفیق...",
                "😡 ارزش عصبی شدن نداره!",
                "🧘 یه نفس عمیق بکش و ولش کن.",
            ],
            "love": [
                "❤️ منم از تو خوشم میاد 😳",
                "😘 خجالت نکش 😅",
                "🌹 عشق توی هوا پخشه!",
            ],
            "question": [
                "🤔 سوال خوبیه، بزار فکر کنم...",
                "😅 سوال سختیه ولی جالبه!",
                "🧠 سوال باعث رشد ذهن میشه!",
            ],
            "neutral": [
                "🙂 جالبه...",
                "😶 باشه...",
                "👌 حله!",
                "🤖 من گوش می‌دم...",
                "😏 ادامه بده..."
            ],
        }

        base = random.choice(responses.get(emotion, responses["neutral"]))
        reply = enhance_sentence(base)
        shadow_learn(text, reply)

        await update.message.reply_text(reply)

    except Exception as e:
        print(f"❌ [smart_response ERROR]: {e}")
        await update.message.reply_text("⚠️ خطای موقتی در پاسخ‌دهی.")
