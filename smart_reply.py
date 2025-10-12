import random

def detect_emotion(text: str) -> str:
    text = text.lower()
    if any(w in text for w in ["غم", "بد", "دلگیر", "ناراحت", "گریه", "تنهام"]):
        return "sad"
    if any(w in text for w in ["خوشحال", "خوبه", "عالی", "خفن", "مرسی"]):
        return "happy"
    if any(w in text for w in ["عصبانی", "حرص", "خفه شو", "برو گمشو"]):
        return "angry"
    if any(w in text for w in ["دوست", "عشق", "دلم", "می‌خوام", "بغل"]):
        return "love"
    return "neutral"

def smart_response(text: str, emotion: str) -> str:
    responses = {
        "sad": [
            "ناراحت نباش 😔 من کنارتم همیشه.",
            "می‌دونم سخته، ولی می‌گذره 🌧️",
            "بیا یه فنجون چای و یه لبخند 😌"
        ],
        "happy": [
            "همینطوری شاد بمون 😍",
            "چه عالی! خوشحالم برات ✨",
            "لبخندت دنیا رو قشنگ‌تر می‌کنه 😄"
        ],
        "angry": [
            "آروم باش 😅 ارزشش رو نداره!",
            "نفسی عمیق بکش 😤",
            "باشه باشه، عصبانی نباش 😅"
        ],
        "love": [
            "عه جدی؟ 🥰 منم دوستت دارم!",
            "احساسات قشنگی داری 💖",
            "عشق همیشه قشنگه 🌹"
        ],
        "neutral": []
    }
    return random.choice(responses.get(emotion, [])) if responses.get(emotion) else None
