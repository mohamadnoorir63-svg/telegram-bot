import json
import os
import random
from fix_memory import fix_json

# 🧩 مسیر فایل‌های اصلی حافظه
FILES = ["memory.json", "shadow_memory.json", "group_data.json"]

# ========================= 📂 آماده‌سازی اولیه =========================
def init_files():
    for f in FILES:
        if not os.path.exists(f):
            with open(f, "w", encoding="utf-8") as file:
                json.dump({"data": {}, "users": []}, file, ensure_ascii=False, indent=2)
    print("✅ فایل‌های حافظه بررسی و ایجاد شدند.")

# ========================= 💾 عملیات پایه حافظه =========================
def load_data(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"⚠️ خطا در {file}، تلاش برای تعمیر خودکار...")
        fixed = fix_json(file)
        if fixed:
            with open(file, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            return {"data": {}, "users": []}

def save_data(file, data):
    try:
        with open(file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ خطا در ذخیره {file}: {e}")

# ========================= 🧠 یادگیری و پاسخ =========================
def learn(phrase, response):
    mem = load_data("memory.json")
    data = mem.get("data", {})

    if phrase not in data:
        data[phrase] = []

    if response not in data[phrase]:
        data[phrase].append(response)
        save_data("memory.json", mem)
        print(f"🧠 یادگیری: {phrase} → {response}")
    else:
        print("⚙️ تکراری، یاد نگرفت.")

def shadow_learn(phrase, response):
    shadow = load_data("shadow_memory.json")
    data = shadow.get("data", {})

    if phrase not in data:
        data[phrase] = []

    if response not in data[phrase]:
        data[phrase].append(response)
        save_data("shadow_memory.json", shadow)

def get_reply(text):
    mem = load_data("memory.json")
    data = mem.get("data", {})

    matches = [k for k in data.keys() if k in text]
    if matches:
        key = random.choice(matches)
        return random.choice(data[key])
    return None

# ========================= ✨ ابزارهای پیشرفته =========================
def get_stats():
    mem = load_data("memory.json")
    total_phrases = len(mem.get("data", {}))
    total_responses = sum(len(v) for v in mem.get("data", {}).values())
    mode = mem.get("mode", "نرمال")
    return {"phrases": total_phrases, "responses": total_responses, "mode": mode}

def set_mode(mode):
    mem = load_data("memory.json")
    mem["mode"] = mode
    save_data("memory.json", mem)

def enhance_sentence(sentence):
    if not sentence:
        return "🤔 نمی‌دونم چی بگم!"
    extras = ["🙂", "😂", "😎", "🤖", "😅", "😉"]
    return sentence + " " + random.choice(extras)

def generate_sentence():
    mem = load_data("memory.json")
    data = mem.get("data", {})
    if not data:
        return "😅 هنوز چیزی بلد نیستم!"
    phrase = random.choice(list(data.keys()))
    resp = random.choice(data[phrase])
    return f"{phrase} → {resp}"
