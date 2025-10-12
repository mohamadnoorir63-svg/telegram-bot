import json
import os
import random

# ======================= 📁 فایل‌ها =======================

def init_files():
    for f in ["memory.json", "shadow_memory.json", "group_data.json", "jokes.json", "fortunes.json"]:
        if not os.path.exists(f):
            with open(f, "w", encoding="utf-8") as file:
                if f.endswith(".json"):
                    json.dump({}, file, ensure_ascii=False, indent=2)

# ======================= 📖 خواندن و ذخیره =======================

def load_data(filename):
    if not os.path.exists(filename):
        return {}
    with open(filename, "r", encoding="utf-8") as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return {}

def save_data(filename, data):
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

# ======================= 🧠 یادگیری =======================

def learn(phrase, reply):
    data = load_data("memory.json")
    if "data" not in data:
        data["data"] = {}
    if phrase not in data["data"]:
        data["data"][phrase] = []
    if reply not in data["data"][phrase]:
        data["data"][phrase].append(reply)
    save_data("memory.json", data)

# یادگیری پنهان (در حالت خاموش)
def shadow_learn(phrase, reply):
    data = load_data("shadow_memory.json")
    if phrase not in data:
        data[phrase] = []
    if reply not in data[phrase]:
        data[phrase].append(reply)
    save_data("shadow_memory.json", data)

# ادغام حافظه پنهان
def merge_shadow_memory():
    shadow = load_data("shadow_memory.json")
    main = load_data("memory.json")
    for phrase, replies in shadow.items():
        if "data" not in main:
            main["data"] = {}
        if phrase not in main["data"]:
            main["data"][phrase] = []
        for r in replies:
            if r not in main["data"][phrase]:
                main["data"][phrase].append(r)
    save_data("memory.json", main)
    save_data("shadow_memory.json", {})

# ======================= 💬 پاسخ =======================

def get_reply(text):
    data = load_data("memory.json").get("data", {})
    if text in data:
        return random.choice(data[text])
    # اگر نداند، پاسخی تصادفی بده
    generic_responses = [
        "واقعاً نمی‌دونم چی بگم 🤔",
        "می‌تونی بیشتر توضیح بدی؟",
        "جالبه! بگو بیشتر بدونم 😅",
        "اوه اینو هنوز یاد نگرفتم 😅"
    ]
    return random.choice(generic_responses)

# ======================= 🎭 مود و جمله =======================

def set_mode(mode):
    data = load_data("memory.json")
    data["mode"] = mode
    save_data("memory.json", data)

def get_stats():
    data = load_data("memory.json")
    phrases = len(data.get("data", {}))
    responses = sum(len(v) for v in data.get("data", {}).values())
    mode = data.get("mode", "نرمال")
    return {"phrases": phrases, "responses": responses, "mode": mode}

# جمله‌سازی تصادفی از حافظه
def generate_sentence():
    data = load_data("memory.json").get("data", {})
    if not data:
        return "هنوز چیزی یاد نگرفتم 😅"
    phrases = list(data.keys())
    part1 = random.choice(phrases)
    part2 = random.choice(random.choice(list(data.values())))
    return f"{part1}... {part2}"

# ======================= ✨ بهبود پاسخ =======================

def enhance_sentence(text):
    if not text:
        return "چی گفتی؟ 😅"
    endings = ["😂", "😎", "🙂", "😅", "🤔", "😉", "❤️"]
    return text.strip() + " " + random.choice(endings)
