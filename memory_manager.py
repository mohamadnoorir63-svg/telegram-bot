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
    data = load_data("memory.json")

    if "data" not in data:
        data["data"] = {}

    phrase = phrase.strip()
    responses = [r.strip() for r in responses if r.strip()]

    if not responses:
        return "❗ هیچ پاسخی برای یادگیری ارسال نشد."

    if phrase not in data["data"]:
        data["data"][phrase] = [{"text": r, "weight": 1} for r in responses]
        save_data("memory.json", data)
        return f"🧠 یاد گرفتم {len(responses)} پاسخ برای '{phrase}'!"

    existing = data["data"][phrase]
    existing_texts = [r["text"] for r in existing]
    added = 0

    for r in responses:
        if r not in existing_texts:
            existing.append({"text": r, "weight": 1})
            added += 1

    save_data("memory.json", data)

    if added > 0:
        return f"😏 اینو بلد بودم ولی {added} پاسخ جدید هم اضافه شد!"
    else:
        return "😅 اینو قبلاً یاد گرفته بودم."


# ========================= 🌙 یادگیری خودکار در سایه =========================
def shadow_learn(phrase, response):
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


# ========================= 💬 پاسخ‌دهی وزنی =========================
def get_reply(text):
    mem = load_data("memory.json")
    data = mem.get("data", {})

    matches = [k for k in data.keys() if k in text]
    if not matches:
        return None

    key = random.choice(matches)
    responses = data[key]

    if isinstance(responses[0], str):
        responses = [{"text": r, "weight": 1} for r in responses]
        data[key] = responses
        save_data("memory.json", mem)

    weights = [r["weight"] for r in responses]
    chosen = random.choices(responses, weights=weights, k=1)[0]
    chosen["weight"] += 1
    save_data("memory.json", mem)

    return chosen["text"]


# ========================= 🧼 تمیزسازی حافظه =========================
def clean_memory():
    data = load_data("memory.json")
    changed = 0

    for phrase, responses in list(data.get("data", {}).items()):
        valid = []
        seen = set()
        for r in responses:
            text = r["text"].strip()
            if len(text) < 2 or text in seen:
                continue
            seen.add(text)
            valid.append(r)
        if len(valid) != len(responses):
            data["data"][phrase] = valid
            changed += 1

    if changed > 0:
        save_data("memory.json", data)
        print(f"🧹 حافظه تمیز شد ({changed} مورد اصلاح شد)")
    return changed


# ========================= 📊 آمار و اطلاعات =========================
def get_stats():
    mem = load_data("memory.json")
    total_phrases = len(mem.get("data", {}))
    total_responses = sum(len(v) for v in mem.get("data", {}).values())
    total_weight = sum(sum(r.get("weight", 1) for r in v) for v in mem.get("data", {}).values())
    mode = mem.get("mode", "نرمال")

    return {
        "phrases": total_phrases,
        "responses": total_responses,
        "total_weight": total_weight,
        "mode": mode
    }


def set_mode(mode):
    mem = load_data("memory.json")
    mem["mode"] = mode
    save_data("memory.json", mem)


# ========================= ✨ جمله‌سازی خلاق =========================
def enhance_sentence(sentence):
    if not sentence:
        return "🤔 نمی‌دونم چی بگم!"
    extras = ["🙂", "😂", "😎", "🤖", "😅", "😉", "✨", "😄"]
    return sentence + " " + random.choice(extras)


def generate_sentence():
    mem = load_data("memory.json")
    data = mem.get("data", {})
    if not data:
        return "😅 هنوز چیزی بلد نیستم!"

    phrases = list(data.keys())
    if len(phrases) < 2:
        phrase = random.choice(phrases)
        resp = random.choice(data[phrase])
        text = resp["text"] if isinstance(resp, dict) else resp
        return f"{phrase} → {text}"

    p1, p2 = random.sample(phrases, 2)
    r1 = random.choice(data[p1])
    r2 = random.choice(data[p2])
    t1 = r1["text"] if isinstance(r1, dict) else r1
    t2 = r2["text"] if isinstance(r2, dict) else r2
    return f"{p1} ولی {t1}، بعدش {t2}"


# ========================= 📋 نمایش لیست جملات =========================
def list_phrases(limit=50):
    mem = load_data("memory.json")
    phrases = list(mem.get("data", {}).keys())
    if not phrases:
        return "😅 هنوز چیزی یاد نگرفتم!"
    show = phrases[:limit]
    return "🧾 جملات یادگرفته‌شده:\n\n" + "\n".join(show)


# ========================= 🧠 تقویت هوشمند حافظه (پیشرفته) =========================
def reinforce_learning(verbose=True):
    """
    تقویت پاسخ‌های مفید و حذف پاسخ‌های ضعیف یا منقضی‌شده
    - بازمی‌گرداند: dict شامل آمار تقویت و حذف پاسخ‌ها
    """
    mem = load_data("memory.json")
    data = mem.get("data", {})
    changed = False
    strengthened, removed = 0, 0

    for phrase, responses in list(data.items()):
        new_responses = []
        for r in responses:
            text = r.get("text", "").strip()
            weight = r.get("weight", 1)

            if len(text) < 2:
                removed += 1
                continue

            # 🔹 افزایش وزن پاسخ‌های طبیعی
            if any(c in text for c in "؟!?!.🙂😂😅🤖😉😎✨❤️💬"):
                new_weight = min(weight + random.choice([1, 2]), 15)
                if new_weight > weight:
                    strengthened += 1
                r["weight"] = new_weight

            # 🔸 کاهش وزن پاسخ‌های بی‌احساس
            elif weight > 1:
                r["weight"] -= 1

            if r["weight"] <= 0:
                removed += 1
                continue

            new_responses.append(r)

        if len(new_responses) != len(responses):
            changed = True
        data[phrase] = new_responses

    if changed:
        mem["data"] = data
        save_data("memory.json", mem)

    if verbose:
        if strengthened or removed:
            print(f"🧠 حافظه تقویت شد → ↑{strengthened} پاسخ قوی‌تر، ↓{removed} پاسخ حذف شد.")
        else:
            print("💤 حافظه نیازی به تقویت نداشت (بهینه بود).")

    return {"strengthened": strengthened, "removed": removed}


# ========================= 🧩 ارزیابی هوش خودکار (AI IQ) =========================
def evaluate_intelligence():
    """
    تحلیل وضعیت مغز ربات و محاسبه‌ی نمره هوش (AI IQ)
    بر اساس:
    - تعداد جملات و پاسخ‌ها
    - میانگین وزن پاسخ‌ها
    """
    mem = load_data("memory.json")
    data = mem.get("data", {})
    if not data:
        return {"iq": 0, "level": "🍼 تازه متولد شده!", "summary": "هیچ داده‌ای هنوز وجود ندارد."}

    total_phrases = len(data)
    total_responses = sum(len(v) for v in data.values())
    total_weight, response_count = 0, 0

    for responses in data.values():
        for r in responses:
            total_weight += r.get("weight", 1)
            response_count += 1

    avg_weight = total_weight / response_count if response_count else 1
    iq_score = int((total_phrases * 0.7 + total_responses * 0.3) * (avg_weight / 3))
    iq_score = min(iq_score, 9999)

    if iq_score < 100:
        level = "🐣 تازه‌کار"
    elif iq_score < 300:
        level = "🧠 در حال رشد"
    elif iq_score < 700:
        level = "⚡ هوش پیشرفته"
    elif iq_score < 1500:
        level = "🚀 خلاق و مستقل"
    else:
        level = "👑 نابغه‌ی خنگول!"

    summary = (
        f"📊 جملات: {total_phrases}\n"
        f"💬 پاسخ‌ها: {total_responses}\n"
        f"⚖️ میانگین وزن پاسخ‌ها: {avg_weight:.2f}\n"
        f"🧩 نمره‌ی هوش (AI IQ): {iq_score}\n"
        f"🌟 سطح: {level}"
    )

    return {"iq": iq_score, "level": level, "summary": summary}
