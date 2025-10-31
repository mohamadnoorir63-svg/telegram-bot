import random
import re
from memory_manager import get_reply, enhance_sentence, shadow_learn
from emotion_memory import remember_emotion, get_last_emotion, emotion_context_reply

# ===============================================================
# تشخیص احساس — Emotion Engine (بدون ایموجی)
# ===============================================================
def detect_emotion(text: str) -> str:
    """تحلیل احساس برای واکنش طبیعی‌تر"""
    if not text:
        return "neutral"

    text = text.lower()

    emotions = {
        "happy": ["خوشحالم", "عالیه", "دمت گرم", "خوبه", "مرسی"],
        "sad": ["غمگینم", "بدم میاد", "دلم گرفته", "افسرده"],
        "angry": ["لعنتی", "حرصم", "عصبانی", "بدبخت", "خفه شو"],
        "love": ["دوستت دارم", "عاشقتم", "عشق", "قلبم"],
        "question": ["?", "چرا", "چیه", "چی شد", "کجایی", "کجا", "چطوری"],
    }

    for emo, words in emotions.items():
        for w in words:
            if w in text:
                return emo

    return "neutral"


# ===============================================================
# پاسخ هوشمند و احساسی — Smart Reply System (بدون ایموجی)
# ===============================================================
def smart_response(text: str, user_id: int) -> str:
    """پاسخ پویا و احساسی بر اساس حافظه و وضعیت کاربر"""
    if not text:
        return ""

    # ۱️⃣ تشخیص احساس فعلی
    emotion = detect_emotion(text)

    # ۲️⃣ بررسی احساس قبلی و واکنش متناسب
    last_emotion = get_last_emotion(user_id)
    context_reply = emotion_context_reply(emotion, last_emotion)
    if context_reply:
        remember_emotion(user_id, emotion)
        return context_reply  # بدون enhance_sentence برای حذف ایموجی

    # ۳️⃣ ثبت احساس فعلی در حافظه
    remember_emotion(user_id, emotion)

    # ⚙️ یادگیری خودکار
    try:
        from ai_learning import auto_learn_from_text
        auto_learn_from_text(text)
    except Exception as e:
        print(f"[Smart Reply] Auto learn skipped: {e}")

    # ۴️⃣ پاسخ‌های پایه برای هر احساس (بدون ایموجی)
    responses = {
        "happy": [
            "خوشحالم حالت خوبه.",
            "خوبه که می‌خندی.",
            "چه حس خوبی.",
            "همیشه بخند تا دنیا بخنده."
        ],
        "sad": [
            "نگران نباش، درست میشه.",
            "بعد شب تاریک، صبح روشن میاد.",
            "دلم برات یه چای داغ می‌خواد."
        ],
        "angry": [
            "آروم باش رفیق.",
            "ارزش عصبی شدن نداره.",
            "یه نفس عمیق بکش و ولش کن."
        ],
        "love": [
            "منم از تو خوشم میاد.",
            "حس خوبیه وقتی یکی اینو میگه.",
            "عشق همیشه زیباست."
        ],
        "question": [
            "سوال خوبیه، بزار فکر کنم...",
            "سوال سختیه ولی جالبه.",
            "سوال باعث رشد ذهن میشه.",
            "شاید جوابش توی حافظه‌م باشه..."
        ],
        "neutral": [
            "جالبه.",
            "باشه.",
            "حله.",
            "من گوش می‌دم.",
            "ادامه بده..."
        ],
    }

    # ۵️⃣ تلاش برای یافتن پاسخ از حافظه
    mem_reply = get_reply(text)
    if mem_reply:
        shadow_learn(text, mem_reply)
        return mem_reply

    # ۶️⃣ اگر پاسخ خاصی پیدا نشد
    if random.random() < 0.3:
        emotion = "neutral"

    base = random.choice(responses.get(emotion, responses["neutral"]))
    reply = base

    # ۷️⃣ ثبت پاسخ در حافظه سایه برای آموزش آینده
    shadow_learn(text, reply)

    return reply
