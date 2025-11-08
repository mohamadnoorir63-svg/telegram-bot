# ai_learning.py
import re
import random
from memory_manager import learn, shadow_learn, load_data, save_data

# ================================
# 🧱 فیلتر ضد ایموجی و متن کوتاه
# ================================
def is_emoji_only(text: str) -> bool:
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
    return not re.sub(emoji_pattern, "", clean)

# ================================
# 🤖 یادگیری خودکار Cloud+
# ================================
def auto_learn_from_text(text: str):
    """یادگیری خودکار از پیام کاربر"""
    if not text or len(text.strip()) < 3:
        return

    if is_emoji_only(text):
        return

    text = text.strip().replace("؟", "?")

    # الگوهای سریع آماده یادگیری
    patterns = {
        r"اسم(ت)? چیه": ["اسمم خنگوله", "من خنگولم"],
        r"چطوری": ["خوبم، تو چطوری؟", "عالیم"],
        r"کجایی": ["اینجام پیش خودت", "همین دور و برم"],
        r"چیکار میکنی": ["دارم یاد می‌گیرم", "در حال رشد مغزمم"],
        r"دوست(م)? داری": ["خیلی زیاد", "آره معلومه"],
        r"کی ساختت": ["یه آدم مهربون", "خودت چی فکر می‌کنی؟"],
        r"ربات(ی)?": ["آره ولی با احساس", "آره ولی شبیه آدمم"],
        r"خنگ(ی)?": ["آره ولی باحال", "آره ولی باهوشم"],
    }

    # بررسی و یادگیری سریع
    for pattern, responses in patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            data = load_data("memory.json").get("data", {})
            if pattern in data:
                existing_texts = [r["text"] if isinstance(r, dict) else r for r in data[pattern]]
                if any(resp in existing_texts for resp in responses):
                    return
            learn(pattern, *responses)
            shadow_learn(text, random.choice(responses))
            return

    # ================================
    # 🧠 یادگیری پویا بدون الگو
    # ================================
    words = text.split()
    if len(words) >= 3:
        key = " ".join(words[:2])
        base_reply = random.choice(["آره", "درسته", "جالبه", "باشه", "اوه"])
        tail = random.choice(words[-2:])
        resp = f"{base_reply} {tail}"

        data = load_data("memory.json").get("data", {})
        if key in data:
            existing = [r["text"] if isinstance(r, dict) else r for r in data[key]]
            if resp in existing:
                return

        # ذخیره در حافظه سایه
        shadow_learn(key, resp)

# ================================
# 🧹 پاکسازی خودکار حافظه سایه
# ================================
def clean_shadow_memory():
    shadow = load_data("shadow_memory.json")
    data = shadow.get("data", {})
    changed = False
    for phrase, responses in list(data.items()):
        if not isinstance(responses, list):
            continue
        cleaned = list({r.strip() for r in responses if r and len(r.strip()) > 2})
        if cleaned != responses:
            data[phrase] = cleaned
            changed = True
    if changed:
        shadow["data"] = data
        save_data("shadow_memory.json", shadow)

# ================================
# 🏋️‍♂️ تقویت خودکار حافظه
# ================================
def reinforce_shadow_memory():
    shadow = load_data("shadow_memory.json")
    data = shadow.get("data", {})
    mem = load_data("memory.json")
    main_data = mem.get("data", {})

    moved = 0
    for phrase, responses in data.items():
        for resp in responses:
            learn(phrase, resp)
            moved += 1

    # پاکسازی حافظه سایه پس از انتقال
    shadow["data"] = {}
    save_data("shadow_memory.json", shadow)
    return moved
