# brain_bridge_group.py
import json
import os
from context_memory import ContextMemory
from emotion_memory import remember_emotion, get_last_emotion, emotion_context_reply
from smart_reply import detect_emotion, smart_response, enhance_sentence
from memory_manager import get_reply  # برای بررسی پاسخ از حافظه

# 📁 فایل ذخیره رفتار گروه‌ها
GROUP_MEMORY_FILE = "group_behavior.json"

# 🧠 حافظه‌ی کوتاه‌مدت گفتگو
context_memory = ContextMemory()

# 🧩 حافظهٔ رفتار گروهی در RAM
group_behavior = {}


def load_group_data():
    """خواندن داده‌های رفتار گروه‌ها از فایل"""
    global group_behavior
    if os.path.exists(GROUP_MEMORY_FILE):
        try:
            with open(GROUP_MEMORY_FILE, "r", encoding="utf-8") as f:
                group_behavior = json.load(f)
        except json.JSONDecodeError:
            print("⚠️ خطا در بارگذاری group_behavior.json، حافظه خالی شد")
            group_behavior = {}
    else:
        group_behavior = {}


def save_group_data():
    """ذخیره رفتار گروه‌ها در فایل"""
    with open(GROUP_MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(group_behavior, f, ensure_ascii=False, indent=2)


def update_group_mood(chat_id: int, emotion: str):
    """به‌روزرسانی مود کلی گروه"""
    chat_key = str(chat_id)
    if chat_key not in group_behavior:
        group_behavior[chat_key] = {"mood": "neutral", "messages": 0}

    data = group_behavior[chat_key]
    data["messages"] += 1

    # تنظیم مود گروه بر اساس احساس فعلی
    moods = {
        "happy": 1,
        "love": 2,
        "neutral": 0,
        "sad": -1,
        "angry": -2
    }

    current = moods.get(data.get("mood", "neutral"), 0)
    change = moods.get(emotion, 0)
    avg = (current + change) / 2

    # 🎭 تعیین مود نهایی
    if avg > 0.5:
        data["mood"] = "funny"
    elif avg < -0.5:
        data["mood"] = "serious"
    else:
        data["mood"] = "neutral"

    save_group_data()


def process_group_message(user_id: int, chat_id: int, text: str):
    """پردازش پیام هوشمند با در نظر گرفتن context، احساس و مود گروه"""
    if not text or not text.strip():
        return "لطفا چیزی بنویسید!"

    # ذخیره پیام در حافظه کوتاه‌مدت
    context_memory.add_message(user_id, text)
    recent_context = context_memory.get_context(user_id)
    if not isinstance(recent_context, list):
        recent_context = []

    # ترکیب آخرین ۳ پیام یا پیام فعلی
    full_context = " ".join(recent_context[-3:]) if recent_context else text

    # تشخیص احساس و ثبت در حافظه احساسی
    current_emotion = detect_emotion(full_context)
    last_emotion = get_last_emotion(user_id)
    remember_emotion(user_id, current_emotion)

    # به‌روزرسانی مود گروه
    update_group_mood(chat_id, current_emotion)

    # بررسی پاسخ احساسی بر اساس context
    emotion_reply = emotion_context_reply(current_emotion, last_emotion)
    if emotion_reply:
        return emotion_reply

    # 🎨 تعیین پاسخ اصلی
    group_mood = group_behavior.get(str(chat_id), {}).get("mood", "neutral")

    # بررسی پاسخ از حافظه ربات
    reply = get_reply(full_context)
    if reply:
        # اگر text لیست بود، اولین آیتم را بگیر
        if isinstance(reply, dict):
            t = reply.get("text")
            if isinstance(t, list):
                reply_text = t[0]
            elif isinstance(t, str):
                reply_text = t
            else:
                reply_text = str(t)
        else:
            reply_text = str(reply)
    else:
        # اگر پاسخی از حافظه نبود، پاسخ هوشمند یا جمله تقویت‌شده
        reply_text = smart_response(full_context, user_id) or enhance_sentence(full_context)

    # 🎭 اعمال مود گروه بر روی پاسخ
    if group_mood == "funny":
        reply_text += " 😂"
    elif group_mood == "serious":
        reply_text = "🤔 " + reply_text

    return reply_text


def clear_user_context(user_id: int):
    """پاک کردن حافظهٔ موقت کاربر"""
    context_memory.clear_context(user_id)


# 🚀 بارگذاری داده‌ها در شروع
load_group_data()
