import json
import os
import random

# مسیر فایل‌های حافظه
MAIN_MEMORY = "memory.json"
SHADOW_MEMORY = "shadow_memory.json"
GROUP_MEMORY = "group_data.json"


# 🧠 اگر فایل‌ها وجود نداشتن، بسازشون
def init_files():
    files = [
        (MAIN_MEMORY, {"replies": {}, "learning": True, "mode": "نرمال"}),
        (SHADOW_MEMORY, {"hidden": {}}),
        (GROUP_MEMORY, {}),
    ]
    for path, data in files:
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)


# 📂 خواندن داده‌ها از فایل
def load_data(file_name):
    if not os.path.exists(file_name):
        init_files()
    with open(file_name, "r", encoding="utf-8") as f:
        return json.load(f)


# 💾 ذخیره داده‌ها در فایل
def save_data(file_name, data):
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# 🔄 گرفتن مود فعلی (شوخ، بی‌ادب، غمگین، نرمال)
def get_mode():
    data = load_data(MAIN_MEMORY)
    return data.get("mode", "نرمال")


# ✍️ تغییر مود
def set_mode(new_mode):
    data = load_data(MAIN_MEMORY)
    data["mode"] = new_mode
    save_data(MAIN_MEMORY, data)


# 💡 یادگیری جمله جدید
def learn(phrase, response):
    data = load_data(MAIN_MEMORY)
    phrase = phrase.lower().strip()
    response = response.strip()

    if phrase not in data["replies"]:
        data["replies"][phrase] = []

    if response not in data["replies"][phrase]:
        data["replies"][phrase].append(response)

    save_data(MAIN_MEMORY, data)


# 🕵️ یادگیری پنهان (وقتی خاموشه)
def shadow_learn(phrase, response):
    data = load_data(SHADOW_MEMORY)
    phrase = phrase.lower().strip()
    response = response.strip()

    if phrase not in data["hidden"]:
        data["hidden"][phrase] = []

    if response and response not in data["hidden"][phrase]:
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


# 🎲 پاسخ تصادفی با fallback هوشمند
def get_reply(text):
    data = load_data(MAIN_MEMORY)
    replies = data.get("replies", {})
    text = text.lower().strip()

    if text in replies:
        return random.choice(replies[text])

    # اگر بلد نبود، یه جمله طبیعی بسازه
    default_replies = [
        "عه جالبه 😅",
        "چی گفتی؟ دوباره بگو 😜",
        "من تازه دارم یاد می‌گیرم 😎",
        "هوم... شاید بعداً بفهمم 🤔",
        "اینو تا حالا نشنیده بودم 😅",
    ]
    return random.choice(default_replies)


# 📊 آمار یادگیری
def get_stats():
    data = load_data(MAIN_MEMORY)
    total_phrases = len(data.get("replies", {}))
    total_responses = sum(len(v) for v in data["replies"].values())
    mode = data.get("mode", "نرمال")
    return {
        "phrases": total_phrases,
        "responses": total_responses,
        "mode": mode,
    }


# 🧩 بهبود طبیعی جمله‌ها (برای طبیعی‌تر شدن)
def enhance_sentence(sentence):
    replacements = {
        "خوب": ["عالی", "باحال", "اوکی", "خفن"],
        "نه": ["نخیر", "اصلاً", "نچ", "هرگز"],
        "آره": ["آرههه", "اوهوم", "قطعاً", "صد در صد"],
        "سلام": ["سلام رفیق 😎", "درود 😄", "هی سلام ✋"],
        "باشه": ["باشه دیگه 😅", "اوکی خب", "قبول 😏"],
    }

    words = sentence.split()
    new_words = []
    for word in words:
        if word in replacements and random.random() < 0.5:
            new_words.append(random.choice(replacements[word]))
        else:
            new_words.append(word)

    return " ".join(new_words)
