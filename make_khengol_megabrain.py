import json, os, zipfile, random

BASE = os.path.dirname(os.path.abspath(__file__))
OUT_JSON = os.path.join(BASE, "memory.json")
OUT_ZIP = os.path.join(BASE, "khengol_brain_4moods.zip")

MOODS = {
    "😎 شوخ": ["😂 خندیدم!", "عه جدی گفتی؟ 😂", "خیلی باحالی 😎"],
    "🫶 احساسی": ["دلم برات تنگ شده 😢", "تو خاصی 💖", "حس خوبی دادی 😍"],
    "😡 تند": ["حرف دهنتو بفهم 😤", "زیاد حرف نزن 😒", "خفه شو 😡"],
    "🧠 عادی": ["آره 🙂", "درسته ✅", "جالبه 🤔"]
}

def auto_learn_from_text(text: str):
    mood = random.choice(list(MOODS.keys()))
    return f"{text}! ({mood})"

phrases = {}
print("🧠 در حال ساخت مغز خنگول فوق‌هوشمند... لطفاً صبر کن")

for i in range(50000):
    base = random.choice(["سلام", "خوبی", "چیکار می‌کنی", "دوستت دارم", "چته", "کجایی"])
    mood, replies = random.choice(list(MOODS.items()))
    response = random.choice(replies)
    if random.random() < 0.3:
        response = auto_learn_from_text(base)
    phrases[f"{base}_{i}"] = [response]

memory_data = {"phrases": phrases}
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(memory_data, f, ensure_ascii=False, indent=2)

with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zipf:
    zipf.write(OUT_JSON, arcname="memory.json")

print(f"✅ مغز ساخته شد با {len(phrases):,} پاسخ!")
print(f"📦 فایل ذخیره شد در: {OUT_ZIP}")
