import json
import os
import random
from datetime import datetime
from fix_memory import fix_json  # ✅ برای تعمیر خودکار JSON خراب

# 🧩 فایل‌های حافظه اصلی
FILES = ["memory.json", "shadow_memory.json", "group_data.json"]

# ========================= 📂 آماده‌سازی اولیه =========================
def init_files():
    """بررسی و ایجاد فایل‌های حافظه در صورت نبود"""
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
    """ذخیره ایمن داده‌ها در فایل"""
    try:
        with open(file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ خطا در ذخیره {file}: {e}")


# ========================= 🧠 یادگیری هوشمند با وزن =========================
def learn(phrase, *responses):
    """یادگیری و ثبت پاسخ‌ها با خروجی نمایشی و رنگی"""
    data = load_data("memory.json")

    if "data" not in data:
        data["data"] = {}

    phrase = phrase.strip()
    responses = [r.strip() for r in responses if r.strip()]

    if not responses:
        return "⚠️ <b>هیچ پاسخی برای یادگیری ارسال نشد.</b>"

    # ✅ جمله‌ی جدید
    if phrase not in data["data"]:
        data["data"][phrase] = [{"text": r, "weight": 1} for r in responses]
        save_data("memory.json", data)
        return (
            f"🧠 <b>یادگیری جدید!</b>\n"
            f"➕ جمله: <code>{phrase}</code>\n"
            f"💬 پاسخ‌ها: {len(responses)} عدد ثبت شد ✅"
        )

    # 🧩 جمله‌ی تکراری ولی پاسخ‌های جدید
    existing = data["data"][phrase]
    existing_texts = [r["text"] for r in existing]
    added = 0

    for r in responses:
        if r not in existing_texts:
            existing.append({"text": r, "weight": 1})
            added += 1

    save_data("memory.json", data)

    if added > 0:
        return (
            f"😏 <b>خاطره‌ی قدیمی به‌روزرسانی شد!</b>\n"
            f"➕ پاسخ‌های تازه: {added}\n"
            f"✨ خنگول باهوش‌تر شد!"
        )
    else:
        return "😅 <b>این جمله رو از قبل بلد بودم!</b>"


# ========================= 🌙 یادگیری خودکار در سایه =========================
def shadow_learn(phrase, response):
    """ذخیره موقت در حافظه سایه"""
    if not phrase or not response:
        return

    shadow = load_data("shadow_memory.json")
    data = shadow.get("data", {})
    phrase, response = phrase.strip(), response.strip()

    if phrase not in data:
        data[phrase] = [response]
    elif response not in data[phrase]:
        data[phrase].append(response)
    else:
        return

    shadow["data"] = data
    save_data("shadow_memory.json", shadow)
    print(f"🌙 [Shadow Learn] '{phrase}' → '{response}'")


# ========================= 💬 پاسخ‌دهی تصادفی و وزنی =========================
def get_reply(text):
    """پیدا کردن پاسخ از حافظه با سیستم وزن‌دهی + انتخاب تصادفی"""
    mem = load_data("memory.json")
    data = mem.get("data", {})

    # 🔍 پیدا کردن جملات مشابه
    matches = [k for k in data.keys() if k in text]
    if not matches:
        return None

    # 🎯 انتخاب تصادفی یکی از کلیدهای مطابق
    key = random.choice(matches)
    responses = data[key]

    # 🩹 پشتیبانی از ساختار قدیمی
    if isinstance(responses[0], str):
        responses = [{"text": r, "weight": 1} for r in responses]
        data[key] = responses
        save_data("memory.json", mem)

    # 🎲 انتخاب تصادفی با توجه به وزن
    weights = [r["weight"] for r in responses]
    chosen = random.choices(responses, weights=weights, k=1)[0]

    # 📈 افزایش وزن پاسخ انتخاب‌شده
    chosen["weight"] = min(chosen.get("weight", 1) + random.randint(1, 3), 15)

    # 📉 کمی کاهش وزن بقیه پاسخ‌ها برای تعادل طبیعی
    for r in responses:
        if r != chosen and r["weight"] > 1:
            r["weight"] -= 1

    save_data("memory.json", mem)

    # 🌟 اضافه کردن حس طبیعی با ایموجی گاه‌به‌گاه
    reply = chosen["text"]
    if random.random() < 0.25:  # 25% احتمال افزودن احساس
        reply += " " + random.choice(["😄", "😉", "😅", "😎", "🤖", "✨", "❤️"])

    return reply


# (🔻 بقیه کد بدون هیچ تغییری 👇 همون نسخه خودت 🔻)
