# brain_bridge_group.py
import json
import os
from context_memory import ContextMemory
from emotion_memory import remember_emotion, get_last_emotion, emotion_context_reply
from smart_reply import detect_emotion, smart_response, enhance_sentence

# 📁 فایل ذخیره رفتار گروه‌ها
GROUP_MEMORY_FILE = "group_behavior.json"

# 🧠 حافظه‌ی کوتاه‌مدت گفتگو
context_memory = ContextMemory()

# 🧩 حافظهٔ رفتار گروهی در حافظه (RAM)
group_behavior = {}


def load_group_data():
    """خواندن داده‌های رفتار گروه‌ها از فایل"""
    global group_behavior
    if os.path.exists(GROUP_MEMORY_FILE):
        try:
            with open(GROUP_MEMORY_FILE, "r", encoding="utf-8") as f:
                group_behavior = json.load(f)
        except json.JSONDecodeError:
            group_behavior = {}
    else:
        group_behavior = {}


def save_group_data():
    """ذخیره رفتار گروه‌ها در فایل"""
    with open(GROUP_MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(group_behavior, f, ensure_ascii=False, indent=2)


def update_group_mood(chat_id: int, emotion: str):
    """به‌روزرسانی مود کلی گروه"""
    if str(chat_id) not in group_behavior:
        group_behavior[str(chat_id)] = {"mood": "neutral", "messages": 0}

    data = group_behavior[str(chat_id)]
    data["messages"] += 1

    # تنظیم مود گروه بر اساس احساس فعلی
    moods = {
        "happy": 1,
        "love": 2,
        "neutral": 0,
        "sad": -1,
        "angry": -2
    }

    current = moods.get(data["mood"], 0)
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
    context_memory.add_message(user_id, text)
    recent_context = context_memory.get_context(user_id)
    full_context = " ".join(recent_context[-3:]) if recent_context else text

    current_emotion = detect_emotion(full_context)
    last_emotion = get_last_emotion(user_id)
    remember_emotion(user_id, current_emotion)

    update_group_mood(chat_id, current_emotion)

    emotion_reply = emotion_context_reply(current_emotion, last_emotion)
    if emotion_reply:
        return emotion_reply

    # 🎨 تعیین لحن بر اساس مود گروه
    group_mood = group_behavior.get(str(chat_id), {}).get("mood", "neutral")
    response = smart_response(full_context, user_id) or enhance_sentence(full_context)

    if group_mood == "funny":
        response += " 😂"
    elif group_mood == "serious":
        response = "🤔 " + response

    return response


def clear_user_context(user_id: int):
    """پاک کردن حافظهٔ موقت کاربر"""
    context_memory.clear_context(user_id)


# 🚀 بارگذاری داده‌ها در شروع
load_group_data()
