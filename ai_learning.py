import json
from memory_manager import load_data, save_data, learn

def auto_learn_from_text(text: str):
    """
    یادگیری خودکار ساده بر اساس الگوی تکرار در گفت‌وگوها.
    اگر جمله چند بار تکرار بشه، خودش به عنوان ورودی جدید ذخیره می‌شه.
    """
    if not text or len(text) < 2:
        return

    data = load_data("auto_learn.json")
    if "patterns" not in data:
        data["patterns"] = {}

    # شمارش تکرار جملات
    text = text.strip().lower()
    data["patterns"][text] = data["patterns"].get(text, 0) + 1

    # اگر زیاد تکرار بشه، یاد می‌گیره
    if data["patterns"][text] >= 3:
        learn(text, f"پاسخ خودکار به '{text}' 🤖")
        data["patterns"][text] = 0  # ریست شمارش

    save_data("auto_learn.json", data)
