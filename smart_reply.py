import random

# ======================= 😄 تشخیص احساس =======================

def detect_emotion(text: str) -> str:
    """تشخیص احساس کلی از متن"""
    text = text.strip().lower()
    if any(w in text for w in ["😢", "غم", "دلگیر", "بد", "ناراحتم", "گریه"]):
        return "sad"
    if any(w in text for w in ["😂", "🤣", "خنده", "باحاله", "باحال", "😁"]):
        return "funny"
    if any(w in text for w in ["😡", "عصبانی", "حرص", "لعنت", "بدم میاد"]):
        return "angry"
    if any(w in text for w in ["❤️", "دوستت دارم", "عشق", "عاشق"]):
        return "love"
    return "neutral"

# ======================= 🧠 پاسخ هوشمند =======================

def smart_response(text: str, emotion: str = "neutral") -> str:
    """تولید پاسخ طبیعی بر اساس احساس تشخیص داده‌شده"""
    responses = {
        "sad": [
            "ناراحت نباش رفیق 😢",
            "همه چی درست میشه ❤️",
            "غم نخور، من کنارت هستم 🤗"
        ],
        "funny": [
            "😂😂 عجب گفتی!",
            "خیلی خندیدم 😆",
            "تو همیشه باحال می‌نویسی 😜"
        ],
        "angry": [
            "آروم باش، اعصاب خودتو خورد نکن 😌",
            "می‌فهمم عصبانی‌ای 😠 ولی آروم‌تر حرف بزن.",
            "یه لیوان آب بخور، آروم شی 😅"
        ],
        "love": [
            "عه جدی؟ 🥰",
            "خیلی قشنگ گفتی 😍",
            "عشق قشنگه ولی مراقب دلت باش ❤️"
        ],
        "neutral": [
            "آره درسته 😄",
            "جالبه 🤔",
            "ادامه بده، دارم گوش میدم 🙂"
        ]
    }

    # انتخاب پاسخ تصادفی بر اساس احساس
    if emotion in responses:
        return random.choice(responses[emotion])
    return random.choice(responses["neutral"])
