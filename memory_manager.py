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

# ========================= 🧠 یادگیری هوشمند =========================
def learn(phrase, *responses):
    """یادگیری هوشمند با تشخیص جمله تکراری، پاسخ جدید و آمار آموزشی"""
    data = load_data("memory.json")

    if "data" not in data:
        data["data"] = {}

    phrase = phrase.strip()
    responses = [r.strip() for r in responses if r.strip()]

    if not responses:
        return "❗ هیچ پاسخی برای یادگیری ارسال نشد."

    # اگه جمله جدید بود
    if phrase not in data["data"]:
        data["data"][phrase] = list(set(responses))
        save_data("memory.json", data)
        return f"🧠 یاد گرفتم {len(responses)} پاسخ برای '{phrase}'!"

    # اگر جمله تکراریه ولی پاسخ‌های جدید داره
    old_responses = set(data["data"][phrase])
    new_responses = [r for r in responses if r not in old_responses]

    if new_responses:
        data["data"][phrase].extend(new_responses)
        save_data("memory.json", data)
        msg = f"😏 اینو بلد بودم!\n"
        msg += f"➕ {len(new_responses)} پاسخ جدید هم اضافه شد."
        return msg

    # اگه هیچ پاسخ جدیدی نبود
    return "😏 اینو بلد بودم!\nهیچ پاسخ جدیدی نداشتی."

# ========================= 🧠 یادگیری در سایه =========================
def shadow_learn(phrase, response):
    """یادگیری غیر فعال (در سایه) برای ذخیره داده‌ها بدون تکرار"""
    shadow = load_data("shadow_memory.json")
    data = shadow.get("data", {})

    if phrase not in data:
        data[phrase] = []

    if response not in data[phrase]:
        data[phrase].append(response)
        save_data("shadow_memory.json", shadow)

# ========================= 💬 پاسخ‌دهی =========================
def get_reply(text):
    mem = load_data("memory.json")
    data = mem.get("data", {})

    matches = [k for k in data.keys() if k in text]
    if matches:
        key = random.choice(matches)
        return random.choice(data[key])
    return None

# ========================= 📊 آمار و اطلاعات =========================
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

# ========================= ✨ بهبود و جمله تصادفی =========================
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

# ========================= 📋 نمایش لیست جملات =========================
def list_phrases(limit=50):
    """برگرداندن لیست جملات یادگرفته‌شده برای دستور 'لیست'"""
    mem = load_data("memory.json")
    phrases = list(mem.get("data", {}).keys())
    if not phrases:
        return "😅 هنوز چیزی یاد نگرفتم!"
    show = phrases[:limit]
    return "🧾 جملات یادگرفته‌شده:\n\n" + "\n".join(show)def shadow_learn(phrase, response):
    """یادگیری خودکار در سایه — یادگیری غیرفعال ولی هوشمند"""
    if not phrase or not response:
        return

    shadow = load_data("shadow_memory.json")
    data = shadow.get("data", {})

    phrase = phrase.strip()
    response = response.strip()

    # اگر جمله جدید بود
    if phrase not in data:
        data[phrase] = [response]
        save_data("shadow_memory.json", shadow)
        print(f"🌙 [Shadow Learn] جمله جدید: '{phrase}' → '{response}'")
        return

    # اگر جمله وجود داشت ولی پاسخ جدید بود
    if response not in data[phrase]:
        data[phrase].append(response)
        save_data("shadow_memory.json", shadow)
        print(f"🌙 [Shadow Learn] پاسخ جدید برای '{phrase}' افزوده شد.")
    else:
        # یاد گرفته بود، اما نیاز به ذخیره دوباره نیست
        print(f"🌙 [Shadow Learn] تکراری بود، رد شد.")
