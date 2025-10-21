# brain_bridge.py
from context_memory import ContextMemory
from emotion_memory import remember_emotion, get_last_emotion, emotion_context_reply
from smart_reply import detect_emotion, smart_response, enhance_sentence

# 🧠 نمونه‌ی حافظه‌ی موقت گفتگو
context_memory = ContextMemory()

def process_user_message(user_id: int, text: str):
    """
    پردازش هوشمند پیام کاربر با در نظر گرفتن context و احساسات
    خروجی: پاسخ متنی هوشمند
    """
    # ثبت پیام جدید در حافظه‌ی موقت
    context_memory.add_message(user_id, text)
    recent_context = context_memory.get_context(user_id)
    full_context = " ".join(recent_context[-3:]) if recent_context else text

    # 🔍 تشخیص احساس فعلی کاربر
    current_emotion = detect_emotion(full_context)
    last_emotion = get_last_emotion(user_id)
    remember_emotion(user_id, current_emotion)

    # 💬 بررسی تغییر احساس
    emotion_change_reply = emotion_context_reply(current_emotion, last_emotion)
    if emotion_change_reply:
        return emotion_change_reply  # پاسخ احساسی در اولویت است

    # 🧩 تولید پاسخ طبیعی بر اساس context
    reply = smart_response(full_context, user_id) or enhance_sentence(full_context)
    return reply


def clear_user_context(user_id: int):
    """پاک کردن حافظه‌ی موقت گفتگو برای یک کاربر"""
    context_memory.clear_context(user_id)
