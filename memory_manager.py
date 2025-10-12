import json
import random
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_MEMORY = os.path.join(BASE_DIR, "memory.json")
SHADOW_MEMORY = os.path.join(BASE_DIR, "shadow_memory.json")
GROUP_MEMORY = os.path.join(BASE_DIR, "group_data.json")

# 🧠 اگر فایل‌ها وجود نداشتن، بسازشون
def init_files():
    for file_name, default_data in [
        (MAIN_MEMORY, {"replies": {}, "learning": True, "mode": "normal"}),
        (SHADOW_MEMORY, {"hidden": {}}),
        (GROUP_MEMORY, {}),
    ]:
        if not os.path.exists(file_name):
            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)

def load_data(file_name):
    with open(file_name, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(file_name, data):
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_mode():
    data = load_data(MAIN_MEMORY)
    return data.get("mode", "normal")

def set_mode(new_mode):
    data = load_data(MAIN_MEMORY)
    data["mode"] = new_mode
    save_data(MAIN_MEMORY, data)

# 💡 یادگیری جدید
def learn(phrase, response):
    data = load_data(MAIN_MEMORY)
    phrase = phrase.lower().strip()
    response = response.strip()

    if phrase not in data["replies"]:
        data["replies"][phrase] = []

    if response not in data["replies"][phrase]:
        data["replies"][phrase].append(response)

    save_data(MAIN_MEMORY, data)

# 🕵️ یادگیری پنهان
def shadow_learn(phrase, response):
    data = load_data(SHADOW_MEMORY)
    phrase = phrase.lower().strip()
    response = response.strip()

    if phrase not in data["hidden"]:
        data["hidden"][phrase] = []

    if response not in data["hidden"][phrase]:
        data["hidden"][phrase].append(response)

    save_data(SHADOW_MEMORY, data)

# 🔁 ترکیب حافظه پنهان
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

# 🎲 پاسخ تصادفی
def get_reply(text):
    data = load_data(MAIN_MEMORY)
    replies = data.get("replies", {})
    text = text.lower().strip()

    if text in replies:
        return random.choice(replies[text])

    return random.choice(["عه", "باشه", "جالبه 😅", "نمی‌دونم والا", "اوه", "هه"])

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

# 🧩 تغییر طبیعی جمله
def enhance_sentence(sentence):
    replacements = {
        "خوب": ["عالی", "باحال", "اوکی"],
        "نه": ["نچ", "اصلاً", "بیخیال"],
        "آره": ["آرههه", "اوهوم", "قطعاً"],
    }

    words = sentence.split()
    new_words = []
    for word in words:
        if word in replacements and random.random() < 0.4:
            new_words.append(random.choice(replacements[word]))
        else:
            new_words.append(word)

    return " ".join(new_words)
