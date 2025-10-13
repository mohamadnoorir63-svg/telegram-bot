import random
import re
from memory_manager import get_reply, enhance_sentence, shadow_learn

# ======================= 😄 تشخیص احساس =======================
def detect_emotion(text: str) -> str:
    """تحلیل پیشرفته احساس جمله برای واکنش طبیعی‌تر"""
    if not text:
        return "neutral"

    text = text.lower()

    emotions = {
        "happy": ["😂", "🤣", "😅", "خوشحالم", "عالیه", "دمت گرم", "خوبه", "مرسی", "❤️"],
        "sad": ["😔", "😢", "غمگینم", "بدم میاد", "دلم گرفته", "افسرده"],
        "angry": ["😡", "لعنتی", "حرصم", "عصبانی", "بدبخت", "خفه شو"],
        "love": ["دوستت دارم", "❤️", "😘", "عاشقتم", "عشق", "قلبم"],
        "question": ["?", "چرا", "چیه", "چی شد", "کجایی", "کجا", "چطوری"]
    }

    for emo, words in emotions.items():
        for w in words:
            if w in text:
                return emo

    return "neutral"

# ======================= 💬 پاسخ هوشمند =======================
def smart_response(text: str, emotion: str) -> str:
    """پاسخ پویا، طبیعی و یادگیرنده بر اساس احساس"""
    if not text:
        return ""

    # پاسخ‌های پایه
    responses = {
        "happy": [
            "😂 خوشحالم حالت خوبه!",
            "😄 بخند که دنیا بخنده!",
            "😁 چه حس خوبی!",
            "✨ همیشه بخند تا دنیا بخنده!"
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
            "💖 عشق توی هوا پخشه!",
            "🌹 حس خوبیه وقتی یکی میگه اینو!"
        ],
        "question": [
            "🤔 سوال خوبیه، بزار فکر کنم...",
            "😅 سوال سختیه ولی جالبه!",
            "🧠 سوال باعث رشد ذهن میشه!",
            "🔍 جواب اینو شاید توی حافظه‌م پیدا کنم..."
        ],
        "neutral": [
            "🙂 جالبه...",
            "😶 باشه...",
            "👌 حله!",
            "🤖 من گوش می‌دم...",
            "😏 ادامه بده..."
        ],
    }

    # تلاش برای پاسخ از حافظه
    mem_reply = get_reply(text)
    if mem_reply:
        shadow_learn(text, mem_reply)
        return enhance_sentence(mem_reply)

    # ۳۰٪ احتمال تغییر مود به خنثی برای طبیعی‌تر شدن
    if random.random() < 0.3:
        emotion = "neutral"

    # پاسخ نهایی ترکیبی از ثابت + بهبود جمله
    base = random.choice(responses.get(emotion, responses["neutral"]))
    return enhance_sentence(base)
