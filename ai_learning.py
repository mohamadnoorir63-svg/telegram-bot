import re
from memory_manager import learn

# ======================= 🧠 یادگیری خودکار =======================

def clean_text(text: str) -> str:
    """پاک‌سازی متن از کاراکترهای اضافی"""
    text = re.sub(r'[^\w\sآ-ی]', '', text)
    return text.strip().lower()

def auto_learn_from_text(text: str):
    """
    یادگیری خودکار از پیام‌ها:
    اگر جمله دارای نشانه‌ی پرسش و پاسخ باشد (مثلاً شامل "؟" یا "!" و جمله بعدی)
    آن را به‌صورت خودکار ذخیره می‌کند.
    """
    if not text or len(text) < 5:
        return

    # بررسی برای ساختار پرسش و پاسخ
    if "؟" in text or "?" in text:
        question = clean_text(text)
        fake_response = "نمیدونم دقیق 😅"
        learn(question, fake_response)

    elif "!" in text:
        exclamation = clean_text(text)
        learn(exclamation, "عه چه جالب! 😄")

    elif text.endswith(("هه", "😂", "😅")):
        learn(clean_text(text), "می‌خندم باهات 😆")

# ======================= 🤫 یادگیری زمینه‌ای =======================

def contextual_learning(prev_message: str, reply_message: str):
    """
    اگر کاربر پاسخی به پیام قبلی داد،
    جمله‌ی قبلی را به‌عنوان «پرسش» و پاسخ فعلی را به‌عنوان «پاسخ» ذخیره می‌کند.
    """
    if not prev_message or not reply_message:
        return

    prev = clean_text(prev_message)
    reply = clean_text(reply_message)
    if len(prev) > 2 and len(reply) > 2:
        learn(prev, reply)
