import random
import re

# ======================= 😄 تشخیص احساس =======================
def detect_emotion(text: str) -> str:
    """تحلیل ساده احساس جمله برای واکنش طبیعی‌تر"""
    if not text:
        return "neutral"

    text = text.lower()

    happy = ["😂", "🤣", "😅", "خوشحالم", "عالیه", "دمت گرم", "خوبه", "مرسی", "❤️"]
    sad = ["😔", "😢", "غمگینم", "بدم میاد", "دلم گرفته", "افسرده"]
    angry = ["😡", "لعنتی", "حرصم", "عصبانی", "بدبخت", "خفه شو"]
    love = ["دوستت دارم", "❤️", "😘", "عاشقتم", "عشق", "قلبم"]
    question = ["?", "چرا", "چیه", "چی شد", "کجایی", "کجا", "چطوری"]

    for w in happy:
        if w in text:
            return "happy"
    for w in sad:
        if w in text:
            return "sad"
    for w in angry:
        if w in text:
            return "angry"
    for w in love:
        if w in text:
            return "love"
    for w in question:
        if w in text:
            return "question"

    return "neutral"

# ======================= 💬 پاسخ هوشمند =======================
def smart_response(text: str, emotion: str) -> str:
    """پاسخ ساده و انسانی‌مانند بر اساس احساس تشخیص داده‌شده"""
    if not text:
        return ""

    responses = {
        "happy": [
            "😂 خوشحالم حالت خوبه!",
            "😄 بخند که دنیا بخنده!",
            "😁 چه حس خوبی!",
        ],
        "sad": [
            "😢 نگران نباش، درست میشه.",
            "💔 همیشه بعد از شب تاریک، صبح روشن میاد.",
            "😔 دلم برات یه چایی داغ می‌خواد.",
        ],
        "angry": [
            "😤 آروم باش رفیق...",
            "😡 هر چی شده ارزش عصبی شدن نداره.",
            "🧘 یه نفس عمیق بکش!",
        ],
        "love": [
            "❤️ منم از تو خوشم میاد 😳",
            "😘 ای بابا خجالت نکش 😅",
            "💖 عشق توی هوا پخشه!",
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
        ],
    }

    # احتمال ۳۰٪ برای پاسخ رندوم از مود خنثی حتی اگر احساس مشخصه
    if random.random() < 0.3:
        emotion = "neutral"

    return random.choice(responses.get(emotion, responses["neutral"]))
