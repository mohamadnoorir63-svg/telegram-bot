import json
import os
import random

# 📂 مسیر فایل‌ها
MEMORY_FILE = "memory.json"
SHADOW_FILE = "shadow_memory.json"
MODE_FILE = "mode.json"

# 📘 مقداردهی اولیه فایل‌ها
def init_files():
    for f, default in [
        (MEMORY_FILE, {"phrases": {}, "users": []}),
        (SHADOW_FILE, {"phrases": {}}),
        (MODE_FILE, {"mode": "نرمال"}),
    ]:
        if not os.path.exists(f):
            save_data(f, default)

# 📖 توابع عمومی
def load_data(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 🧠 یادگیری جمله و پاسخ‌ها
def learn(phrase, response):
    data = load_data(MEMORY_FILE)
    if phrase not in data["phrases"]:
        data["phrases"][phrase] = []
    if response not in data["phrases"][phrase]:
        data["phrases"][phrase].append(response)
    save_data(MEMORY_FILE, data)

def shadow_learn(phrase, response):
    data = load_data(SHADOW_FILE)
    if phrase not in data["phrases"]:
        data["phrases"][phrase] = []
    if response not in data["phrases"][phrase]:
        data["phrases"][phrase].append(response)
    save_data(SHADOW_FILE, data)

def merge_shadow_memory():
    main = load_data(MEMORY_FILE)
    shadow = load_data(SHADOW_FILE)
    for k, v in shadow.get("phrases", {}).items():
        if k not in main["phrases"]:
            main["phrases"][k] = v
        else:
            for item in v:
                if item not in main["phrases"][k]:
                    main["phrases"][k].append(item)
    save_data(MEMORY_FILE, main)
    save_data(SHADOW_FILE, {"phrases": {}})

# 💬 تولید پاسخ
def get_reply(text):
    data = load_data(MEMORY_FILE)
    phrases = data.get("phrases", {})
    mode = get_mode()
    text = text.strip()

    # جستجوی دقیق
    if text in phrases:
        return random.choice(phrases[text])

    # جستجوی نسبی (در جمله‌ها)
    for key in phrases.keys():
        if key in text or text in key:
            return random.choice(phrases[key])

    # اگر هیچی پیدا نشد جمله‌سازی هوشمند
    return ai_generate_sentence(text, mode)

# 🧩 مود ربات
def get_mode():
    data = load_data(MODE_FILE)
    return data.get("mode", "نرمال")

def set_mode(mood):
    save_data(MODE_FILE, {"mode": mood})

# 📊 آمار
def get_stats():
    data = load_data(MEMORY_FILE)
    phrases = data.get("phrases", {})
    total_responses = sum(len(v) for v in phrases.values())
    return {"phrases": len(phrases), "responses": total_responses, "mode": get_mode()}

# ✨ بهبود پاسخ‌ها
def enhance_sentence(reply):
    if not reply or len(reply) < 2:
        return "نمیدونم چی بگم 🤔"

    adds = ["😂", "😅", "😎", "🙂", "😜", "😉"]
    ends = ["!", "!!", "🤖", "😄"]
    if not reply.endswith(tuple(ends)):
        reply += " " + random.choice(adds)
    return reply

# 🤖 ساخت جمله هوشمند (AI ساده)
def ai_generate_sentence(text, mode):
    words = ["دوست", "زندگی", "حرف", "حوصله", "خنده", "عشق", "دلم"]
    base = random.choice([
        f"نمیدونم {text} یعنی چی 😅",
        f"آره {text} خیلی جالبه!",
        f"در مورد {text} زیاد شنیدم!",
        f"{text}؟ عجب سوالی پرسیدی 😄",
        f"منم به {random.choice(words)} فکر می‌کردم!"
    ])

    if mode == "بی‌ادب":
        base += " برو پی کارت 😏"
    elif mode == "غمگین":
        base = base.replace("😄", "😔").replace("جالبه", "غم‌انگیزه")
    elif mode == "شوخ":
        base += " 😂"

    return base
