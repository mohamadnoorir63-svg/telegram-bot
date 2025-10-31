import re
import random
from memory_manager import learn, load_data, save_data, shadow_learn

# ===============================================================
# 🤖 یادگیری خودکار خنگول Cloud+ — نسخه‌ی بدون ایموجی
# ===============================================================
def auto_learn_from_text(text: str):
    """یادگیری خودکار از گفت‌وگوهای طبیعی کاربران با درک احساس و منطق ساده"""
    # ⚙️ import داخلی برای جلوگیری از حلقه‌ی import
    try:
        from smart_reply import detect_emotion
    except ImportError:
        detect_emotion = lambda x: None  # اگر در دسترس نبود، احساس رو خنثی کن

    if not text or len(text) < 3:
        return

    text = text.strip().replace("؟", "?")
    emotion = detect_emotion(text)  # تشخیص احساس جمله (شاد، غمگین، عصبی، خنثی)

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
            learn(pattern, *responses)
            shadow_learn(text, random.choice(responses))
            return

    # ===============================================================
    # 🧠 یادگیری پویا — بدون الگوی از پیش تعیین‌شده
    # ===============================================================
    words = text.split()
    if len(words) >= 3:
        # کلید اصلی از دو واژه اول جمله ساخته میشه (بهتر از فقط یک کلمه)
        key = " ".join(words[:2])
        base_reply = random.choice(["آره", "درسته", "جالبه", "باشه", "اوه"])
        tail = random.choice(words[-2:])

        # بر اساس احساس، لحن پاسخ رو تغییر بده (بدون ایموجی)
        if emotion == "شاد":
            resp = f"{base_reply} {tail}"
        elif emotion == "غمگین":
            resp = f"{base_reply} {tail}"
        elif emotion == "عصبی":
            resp = f"{base_reply.upper()}"
        else:
            resp = f"{base_reply} {tail}"

        shadow_learn(key, resp)


# ===============================================================
# 🧹 پاک‌سازی هوشمند حافظه (نسخه پیشرفته)
# ===============================================================
def clean_duplicates():
    """حذف تکراری‌ها + پاسخ‌های بی‌فایده و بهینه‌سازی داده‌ها"""
    mem = load_data("memory.json")

    # سازگار با هر نوع ساختار حافظه
    data = mem.get("data") or mem.get("phrases") or {}
    if not data:
        return

    changed = False
    for phrase, responses in list(data.items()):
        if not isinstance(responses, list):
            continue

        # حذف پاسخ‌های تکراری و خالی
        cleaned = list({r.strip() for r in responses if r and len(r.strip()) > 1})

        # حذف پاسخ‌های بسیار کوتاه مثل "آه" یا "ها"
        cleaned = [r for r in cleaned if len(r) > 2]

        # در صورت تغییر ذخیره مجدد
        if cleaned != responses:
            data[phrase] = cleaned
            changed = True

    if changed:
        # ذخیره‌سازی تمیز در همان ساختار اصلی
        if "data" in mem:
            mem["data"] = data
        elif "phrases" in mem:
            mem["phrases"] = data
        save_data("memory.json", mem)
        print("حافظه تمیز و بهینه شد.")


# ===============================================================
# 🧩 بهینه‌سازی و رشد خودکار هوش مصنوعی
# ===============================================================
def reinforce_learning():
    """
    الگوریتم رشد تدریجی — پاسخ‌هایی که چند بار دیده شدن تقویت می‌شن.
    باعث میشه پاسخ‌های پرتکرار قوی‌تر و طبیعی‌تر شن.
    """
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

    # حذف داده‌های بی‌استفاده
    for phrase in list(weights.keys()):
        if weights[phrase] <= 0.5:
            removed += 1
            del weights[phrase]

    mem["weights"] = weights
    save_data("memory.json", mem)
    print(f"تقویت حافظه انجام شد ({strengthened} تقویت، {removed} حذف).")

    return {"strengthened": strengthened, "removed": removed}
