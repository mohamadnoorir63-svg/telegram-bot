import re
import random
from memory_manager import learn, load_data, save_data, shadow_learn

# ===============================================================
# 🧱 فیلتر ضد ایموجی و ضد تکرار
# ===============================================================
def is_emoji_only(text: str) -> bool:
    """بررسی اینکه آیا متن فقط شامل ایموجی یا علامت است"""
    if not text or not text.strip():
        return True

    clean = re.sub(r"[ \n\t.,!?؛،~\-_=+\[\]{}()<>0-9a-zA-Zء-ی]", "", text)
    emoji_pattern = re.compile(
        "["u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002700-\U000027BF"
        u"\U0001F900-\U0001F9FF"
        "]+", flags=re.UNICODE,
    )

    # اگر بعد از حذف ایموجی چیزی نماند، یعنی فقط ایموجی بوده
    return not re.sub(emoji_pattern, "", clean)


# ===============================================================
# 🤖 یادگیری خودکار خنگول Cloud+ — نسخه‌ی ضد ایموجی و ضد تکرار
# ===============================================================
def auto_learn_from_text(text: str):
    """یادگیری خودکار از گفت‌وگوهای طبیعی کاربران با درک احساس و منطق ساده"""
    try:
        from smart_reply import detect_emotion
    except ImportError:
        detect_emotion = lambda x: None

    if not text or len(text.strip()) < 3:
        return

    # 🚫 جلوگیری از یادگیری از ایموجی‌ها
    if is_emoji_only(text):
        return

    text = text.strip().replace("؟", "?")
    emotion = detect_emotion(text)

    # ==============================
    # 🎯 الگوهای آماده یادگیری سریع
    # ==============================
    patterns = {
        r"اسم(ت)? چیه": ["اسمم خنگوله", "من خنگولم"],
        r"چطوری": ["خوبم، تو چطوری؟", "عالیم", "رو فرمم"],
        r"کجایی": ["اینجام پیش خودت", "همین دور و برم"],
        r"چیکار میکنی": ["دارم یاد می‌گیرم", "در حال رشد مغزمم"],
        r"دوست(م)? داری": ["خیلی زیاد", "آره معلومه"],
        r"کی ساختت": ["یه آدم مهربون", "خودت چی فکر می‌کنی؟"],
        r"ربات(ی)?": ["آره ولی با احساس", "آره ولی شبیه آدمم"],
        r"خنگ(ی)?": ["آره ولی باحال", "آره ولی باهوشم"],
    }

    # 🧩 بررسی و یادگیری سریع بر اساس الگوها
    for pattern, responses in patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            mem = load_data("memory.json")
            data = mem.get("data", {})

            # 🚫 جلوگیری از ذخیره تکراری
            if pattern in data:
                existing_texts = [r["text"] if isinstance(r, dict) else r for r in data[pattern]]
                if any(resp in existing_texts for resp in responses):
                    return

            learn(pattern, *responses)
            shadow_learn(text, random.choice(responses))
            return

    # ===============================================================
    # 🧠 یادگیری پویا — بدون الگوی از پیش تعیین‌شده
    # ===============================================================
    words = text.split()
    if len(words) >= 3:
        key = " ".join(words[:2])
        base_reply = random.choice(["آره", "درسته", "جالبه", "باشه", "اوه"])
        tail = random.choice(words[-2:])

        # بر اساس احساس، لحن پاسخ رو تغییر بده
        if emotion == "شاد":
            resp = f"{base_reply} {tail}"
        elif emotion == "غمگین":
            resp = f"{base_reply} {tail}"
        elif emotion == "عصبی":
            resp = f"{base_reply.upper()}"
        else:
            resp = f"{base_reply} {tail}"

        # 🚫 جلوگیری از ذخیره تکراری
        mem = load_data("memory.json")
        data = mem.get("data", {})
        if key in data:
            existing = [r["text"] if isinstance(r, dict) else r for r in data[key]]
            if resp in existing:
                return

        shadow_learn(key, resp)


# ===============================================================
# 🧹 پاک‌سازی هوشمند حافظه
# ===============================================================
def clean_duplicates():
    """حذف تکراری‌ها + پاسخ‌های بی‌فایده و بهینه‌سازی داده‌ها"""
    mem = load_data("memory.json")
    data = mem.get("data") or mem.get("phrases") or {}
    if not data:
        return

    changed = False
    for phrase, responses in list(data.items()):
        if not isinstance(responses, list):
            continue

        # حذف پاسخ‌های تکراری و خالی
        cleaned = list({r.strip() for r in responses if r and len(r.strip()) > 1})

        # حذف پاسخ‌های بسیار کوتاه
        cleaned = [r for r in cleaned if len(r) > 2]

        if cleaned != responses:
            data[phrase] = cleaned
            changed = True

    if changed:
        if "data" in mem:
            mem["data"] = data
        elif "phrases" in mem:
            mem["phrases"] = data
        save_data("memory.json", mem)
        print("حافظه تمیز و بهینه شد.")


# ===============================================================
# 🧩 رشد تدریجی هوش مصنوعی
# ===============================================================
def reinforce_learning():
    """افزایش وزن پاسخ‌های پرتکرار و حذف موارد ضعیف"""
    mem = load_data("memory.json")
    data = mem.get("data") or mem.get("phrases") or {}
    weights = mem.get("weights", {})

    strengthened = 0
    removed = 0

    for phrase, responses in data.items():
        if not isinstance(responses, list):
            continue
        count = len(responses)
        old_weight = weights.get(phrase, 1)
        new_weight = min(old_weight + count / 5, 20)
        if new_weight != old_weight:
            strengthened += 1
        weights[phrase] = new_weight

    for phrase in list(weights.keys()):
        if weights[phrase] <= 0.5:
            removed += 1
            del weights[phrase]

    mem["weights"] = weights
    save_data("memory.json", mem)
    print(f"تقویت حافظه انجام شد ({strengthened} تقویت، {removed} حذف).")

    return {"strengthened": strengthened, "removed": removed}
