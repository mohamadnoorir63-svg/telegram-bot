import json
import random
import os

# 📂 مسیر فایل‌های حافظه
MAIN_MEMORY = "memory.json"
SHADOW_MEMORY = "shadow_memory.json"
GROUP_MEMORY = "group_data.json"


# 🧠 ایجاد فایل‌ها در صورت نبودن
def init_files():
    for file_name, default_data in [
        (MAIN_MEMORY, {"replies": {}, "learning": True, "mode": "normal"}),
        (SHADOW_MEMORY, {"hidden": {}}),
        (GROUP_MEMORY, {}),
    ]:
        if not os.path.exists(file_name):
            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)


# 📖 خواندن داده‌ها از فایل
def load_data(file_name):
    with open(file_name, "r", encoding="utf-8") as f:
        return json.load(f)


# 💾 ذخیره داده‌ها در فایل
def save_data(file_name, data):
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# 🎭 گرفتن مود فعلی (شوخ، بی‌ادب، غمگین، نرمال)
def get_mode():
    data = load_data(MAIN_MEMORY)
    return data.get("mode", "normal")


# ✍️ تغییر مود فعلی
def set_mode(new_mode):
    data = load_data(MAIN_MEMORY)
    data["mode"] = new_mode
    save_data(MAIN_MEMORY, data)


# 💡 یادگیری جمله و پاسخ جدید
def learn(phrase, response):
    data = load_data(MAIN_MEMORY)
    phrase = phrase.lower().strip()
    response = response.strip()

    if "replies" not in data:
        data["replies"] = {}

    if phrase not in data["replies"]:
        data["replies"][phrase] = []

    if response not in data["replies"][phrase]:
        data["replies"][phrase].append(response)

    save_data(MAIN_MEMORY, data)


# 🕵️ یادگیری پنهان (وقتی ربات خاموشه)
def shadow_learn(phrase, response):
    data = load_data(SHADOW_MEMORY)
    phrase = phrase.lower().strip()
    response = response.strip()

    if "hidden" not in data:
        data["hidden"] = {}

    if phrase not in data["hidden"]:
        data["hidden"][phrase] = []

    if response not in data["hidden"][phrase]:
        data["hidden"][phrase].append(response)

    save_data(SHADOW_MEMORY, data)


# 🔁 ادغام حافظه پنهان با اصلی
def merge_shadow_memory():
    main = load_data(MAIN_MEMORY)
    shadow = load_data(SHADOW_MEMORY)

    for phrase, replies in shadow.get("hidden", {}).items():
        if phrase not in main["replies"]:
            main["replies"][phrase] = replies
        else:
            for r in replies:
                if r not in main["replies"][phrase]:
                    main["replies"][phrase].append(r)

    shadow["hidden"] = {}
    save_data(MAIN_MEMORY, main)
    save_data(SHADOW_MEMORY, shadow)


# 🎲 گرفتن پاسخ تصادفی
def get_reply(text):
    data = load_data(MAIN_MEMORY)
    replies = data.get("replies", {})
    text = text.lower().strip()

    if text in replies:
        return random.choice(replies[text])

    # اگر جمله‌ای بلد نبود، خودش یه جواب بسازه 😄
    random_words = ["عه 😅", "جدی میگی؟", "اوهوم", "نمی‌دونم والا", "باحاله 😎", "عه، جالبه!"]
    return random.choice(random_words)


# 📊 آمار حافظه
def get_stats():
    data = load_data(MAIN_MEMORY)
    total_phrases = len(data.get("replies", {}))
    total_responses = sum(len(v) for v in data["replies"].values())
    mode = data.get("mode", "normal")
    return {
        "phrases": total_phrases,
        "responses": total_responses,
        "mode": mode,
    }


# ✨ بهبود طبیعی جملات (ادبیات متفاوت)
def enhance_sentence(sentence):
    replacements = {
        "خوب": ["عالی", "باحال", "اوکی"],
        "نه": ["نچ", "اصلاً", "نخیر"],
        "آره": ["آرههه", "اوهوم", "قطعاً"],
        "سلام": ["سلام سلام! 😁", "درود بر تو!", "سلام به روی ماهت 😎"]
    }

    words = sentence.split()
    new_words = []
    for word in words:
        if word in replacements and random.random() < 0.4:
            new_words.append(random.choice(replacements[word]))
        else:
            new_words.append(word)

    return " ".join(new_words)
