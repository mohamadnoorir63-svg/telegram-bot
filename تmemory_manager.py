import json
import os
import random
from datetime import datetime
from fix_memory import fix_json  # برای تعمیر خودکار JSON خراب

# فایل‌های حافظه اصلی
FILES = ["memory.json", "shadow_memory.json", "group_data.json"]

# ========================= آماده‌سازی اولیه =========================

def init_files():
    """بررسی و ایجاد فایل‌های حافظه در صورت نبود"""
    for f in FILES:
        if not os.path.exists(f):
            with open(f, "w", encoding="utf-8") as file:
                json.dump({"data": {}, "users": []}, file, ensure_ascii=False, indent=2)
    print("فایل‌های حافظه بررسی و ایجاد شدند.")

# ========================= عملیات پایه حافظه =========================

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
        print(f"⚠️ خطا در ذخیره {file}: {e}")

# ========================= یادگیری هوشمند با وزن =========================

def learn(phrase, *responses):
    """یادگیری و ثبت پاسخ‌ها با خروجی نمایشی"""
    data = load_data("memory.json")
    if "data" not in data:
        data["data"] = {}

    phrase = phrase.strip()
    responses = [r.strip() for r in responses if r.strip()]

    if not responses:
        return "<b>هیچ پاسخی برای یادگیری ارسال نشد.</b>"

    # جمله‌ی جدید
    if phrase not in data["data"]:
        data["data"][phrase] = [{"text": r, "weight": 1} for r in responses]
        save_data("memory.json", data)
        return (
            f"<b>یادگیری جدید!</b>\n"
            f"➕ جمله: <code>{phrase}</code>\n"
            f"پاسخ‌ها: {len(responses)} عدد ثبت شد"
        )

    # جمله‌ی تکراری ولی پاسخ‌های جدید
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
            f"<b>خاطره‌ی قدیمی به‌روزرسانی شد!</b>\n"
            f"پاسخ‌های تازه: {added}\n"
            f"به‌روزرسانی انجام شد."
        )
    else:
        return "<b>این جمله را از قبل بلد بودم!</b>"
        # ========================= یادگیری چندخطی =========================
def long_learn(phrase, *lines):
    """
    یادگیری چندخطی به عنوان یک پاسخ واحد با قاب عاشقانه.
    مثال:
        طولانی یادبگیر عاشقانه
        خط اول
        خط دوم
        خط سوم
    """
    data = load_data("memory.json")
    if "data" not in data:
        data["data"] = {}

    phrase = phrase.strip()
    lines = [line.strip() for line in lines if line.strip()]
    if not lines:
        return "<b>هیچ متنی برای یادگیری ارسال نشد.</b>"

    # ترکیب تمام خطوط به یک پاسخ واحد
    combined_response = "\n".join(lines)

    # اضافه کردن قاب عاشقانه
    decorated_response = (
    "🖤──────༺♡༻──────💔\n"
    + combined_response + "\n"
    "💔──────༺♡༻──────🖤"
    )

    # ذخیره در حافظه
    if phrase not in data["data"]:
        data["data"][phrase] = [{"text": decorated_response, "weight": 1}]
        save_data("memory.json", data)
        return f"<b>یادگیری جدید چندخطی!</b>\n➕ جمله: <code>{phrase}</code>\nپاسخ قاب‌دار ثبت شد."
    
    # اگر قبلاً بود ولی پاسخ جدید بود
    existing_texts = [r["text"] for r in data["data"][phrase]]
    if decorated_response not in existing_texts:
        data["data"][phrase].append({"text": decorated_response, "weight": 1})
        save_data("memory.json", data)
        return f"<b>خاطره‌ی قدیمی به‌روزرسانی شد!</b>\nپاسخ قاب‌دار جدید اضافه شد."
    
    return "<b>این جمله قاب‌دار را از قبل بلد بودم!</b>"

# ========================= یادگیری خودکار در سایه =========================

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
    print(f"[Shadow Learn] '{phrase}' → '{response}'")

# ========================= پاسخ‌دهی وزنی =========================
def get_reply(text):
    """پیدا کردن پاسخ از حافظه با سیستم وزن‌دهی (نسخه مقاوم‌تر)."""
    mem = load_data("memory.json")
    data = mem.get("data", {})

    # پیدا کردن کلیدهایی که در متن وجود دارند
    matches = [k for k in data.keys() if k in text]
    if not matches:
        return None

    # سعی می‌کنیم از بین matches یکی یکی انتخاب کنیم تا اگر جمله‌ای خراب بود از بقیه استفاده شود
    random.shuffle(matches)
    changed = False

    for key in matches:
        responses = data.get(key, [])

        # اگر لیست پاسخ‌ها خالی است => جمله را پاک کن و برو سراغ بعدی
        if not responses:
            if key in data:
                del data[key]
                changed = True
            continue

        # نرمال‌سازی: اگر ساختار قدیمی (رشته) بود تبدیل به دیکت کنیم
        try:
            if isinstance(responses[0], str):
                responses = [{"text": r, "weight": 1} for r in responses]
                data[key] = responses
                changed = True
        except Exception:
            # اگر دسترسی responses[0] خطا داد، جمله را حذف میکنیم و ادامه میدیم
            if key in data:
                del data[key]
                changed = True
            continue

        # مطمئن شویم همه آیتم‌ها دیکت با کلید text و weight هستند
        cleaned = []
        for r in responses:
            if isinstance(r, dict):
                text_field = r.get("text") or r.get("value") or ""
                weight = r.get("weight", 1)
                try:
                    weight = int(weight)
                except Exception:
                    weight = 1
                cleaned.append({"text": str(text_field), "weight": max(1, weight)})
            else:
                # اگر مورد ناهمگون پیدا شد، تبدیلش کن
                cleaned.append({"text": str(r), "weight": 1})

        if not cleaned:
            # اگر بعد از پاکسازی خالی شد، حذف کن و برو سراغ بعدی
            if key in data:
                del data[key]
                changed = True
            continue

        # محاسبه وزن‌ها — اگر همه صفر بودند وزن یکسان بگذار
        weights = [max(0, int(r.get("weight", 1))) for r in cleaned]
        if sum(weights) == 0:
            weights = [1] * len(weights)

        # انتخاب ایمن با try/except
        try:
            chosen = random.choices(cleaned, weights=weights, k=1)[0]
        except Exception:
            # اگر به هر دلیل خطا شد، fallback به اولین پاسخ
            chosen = cleaned[0]

        # افزایش وزن و ذخیره
        try:
            for r in cleaned:
                if r["text"] == chosen["text"]:
                    r["weight"] = r.get("weight", 1) + 1
                    break
            data[key] = cleaned
            save_data("memory.json", mem)
        except Exception:
            # اگر ذخیره مشکل داشت، حداقل پاسخ را برگردان
            return chosen["text"]

        return chosen["text"]

    # اگر تغییراتی داشتیم آنها را ذخیره کن
    if changed:
        save_data("memory.json", mem)

    return None


# ========================= تمیزسازی حافظه =========================

def clean_memory():
    """حذف پاسخ‌های تکراری، کوتاه و بی‌فایده"""
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

# ========================= آمار و اطلاعات =========================

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

# ========================= جمله‌سازی خلاق =========================

def enhance_sentence(sentence):
    if not sentence:
        return "نمی‌دانم چه بگویم!"
    return sentence

def generate_sentence():
    """ترکیب دو جمله تصادفی برای ساخت پاسخ جدید"""
    mem = load_data("memory.json")
    data = mem.get("data", {})
    if not data:
        return "هنوز چیزی بلد نیستم!"

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
    # ========================= مدیریت صف جملات برای عدم تکرار =========================
_sentence_queue = []

def get_random_sentence_no_repeat():
    """
    برگرداندن یک جمله تصادفی بدون تکرار تا تمام جملات استفاده شوند.
    وقتی تمام جملات مصرف شد، دوباره لیست shuffle می‌شود.
    """
    global _sentence_queue
    mem = load_data("memory.json")
    data = mem.get("data", {})

    phrases = list(data.keys())
    if not phrases:
        return "هنوز چیزی بلد نیستم!"

    # ساخت صف جدید اگر خالی باشد
    if not _sentence_queue:
        _sentence_queue = phrases.copy()
        random.shuffle(_sentence_queue)

    # برداشتن اولین جمله از صف
    phrase = _sentence_queue.pop(0)
    responses = data.get(phrase, [])

    # اگر پاسخ دارد، یکی را انتخاب کن
    if responses:
        r = random.choice(responses)
        text = r["text"] if isinstance(r, dict) else r
        return f"{phrase} → {text}"
    else:
        # اگر پاسخی ندارد، برو سراغ بعدی (بازگشتی)
        return get_random_sentence_no_repeat()

# ========================= لیست زیبا از جملات =========================

def list_phrases(limit=50):
    """نمایش فهرست جملات یادگرفته‌شده"""
    mem = load_data("memory.json")
    phrases = list(mem.get("data", {}).keys())

    if not phrases:
        return "هنوز چیزی یاد نگرفتم!"

    show = phrases[:limit]
    text = "<b>فهرست جملات یادگرفته‌شده:</b>\n\n"

    for i, phrase in enumerate(show, 1):
        text += f"{i}. <code>{phrase}</code>\n"

    text += f"\nدر مجموع {len(phrases)} جمله در حافظه وجود دارد."
    return text

# ========================= تقویت حافظه (پیشرفته) =========================

def reinforce_learning(verbose=True):
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

            # افزایش وزن پاسخ‌های طبیعی
            if any(c in text for c in "؟!?!."):
                new_weight = min(weight + random.choice([1, 2]), 15)
                if new_weight > weight:
                    strengthened += 1
                r["weight"] = new_weight

            # کاهش وزن پاسخ‌های بی‌احساس
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
            print(f"🧠 حافظه تقویت شد → {strengthened} پاسخ قوی‌تر، {removed} پاسخ حذف شد.")
        else:
            print("✅ حافظه نیازی به تقویت نداشت.")
    return {"strengthened": strengthened, "removed": removed}

# ========================= ارزیابی هوش خودکار =========================

def evaluate_intelligence():
    mem = load_data("memory.json")
    data = mem.get("data", {})
    if not data:
        return {"iq": 0, "level": "تازه متولد شده", "summary": "هنوز چیزی یاد نگرفته‌ام."}

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
        level = "تازه‌کار"
    elif iq_score < 300:
        level = "در حال رشد"
    elif iq_score < 700:
        level = "هوش پیشرفته"
    elif iq_score < 1500:
        level = "خلاق و مستقل"
    else:
        level = "نابغه"

    summary = (
        f"جملات: {total_phrases}\n"
        f"پاسخ‌ها: {total_responses}\n"
        f"میانگین وزن پاسخ‌ها: {avg_weight:.2f}\n"
        f"نمره‌ی هوش (AI IQ): {iq_score}\n"
        f"سطح: {level}"
    )

    return {"iq": iq_score, "level": level, "summary": summary}

# ========================= حذف جمله از حافظه =========================
# ========================= حذف جمله از حافظه =========================

def delete_phrase(phrase, partial=False):
    """حذف یک جمله یا چند جمله‌ی مشابه از حافظه"""
    phrase = phrase.strip()
    data = load_data("memory.json")

    if "data" not in data:
        return "<b>حافظه خالی است.</b>"

    found = []
    keys = list(data["data"].keys())

    if partial:
        found = [k for k in keys if phrase in k]
    elif phrase in data["data"]:
        found = [phrase]

    if not found:
        return f"<b>هیچ جمله‌ای شامل '{phrase}' پیدا نشد.</b>"

    for k in found:
        del data["data"][k]

    save_data("memory.json", data)
    return f"<b>{len(found)} جمله حذف شد:</b>\n" + "\n".join(f"- {k}" for k in found)


# ========================= حذف پاسخ مشخص از همه جملات =========================

def delete_response(response_text):
    """
    حذف یک پاسخ خاص از تمام جملات حافظه
    response_text: متنی که باید حذف شود
    """
    response_text = response_text.strip()
    data = load_data("memory.json")

    if "data" not in data:
        return "<b>حافظه خالی است.</b>"

    removed_count = 0
    for phrase, responses in data["data"].items():
        # فیلتر کردن پاسخ‌ها
        new_responses = [r for r in responses if r.get("text", r) != response_text]
        if len(new_responses) != len(responses):
            data["data"][phrase] = new_responses
            removed_count += len(responses) - len(new_responses)

    if removed_count == 0:
        return f"<b>پاسخ '{response_text}' در حافظه پیدا نشد.</b>"

    save_data("memory.json", data)
    return f"<b>پاسخ '{response_text}' از {removed_count} مورد حذف شد!</b>"


# ========================= ارسال پیام ایمن در تلگرام =========================

def safe_send_message(bot, chat_id, text, reply_to_message=None, **kwargs):
    """
    ارسال پیام ایمن در تلگرام بدون کرش کردن ربات.
    - bot: شیء ربات
    - chat_id: شناسه چت
    - text: متن پیام
    - reply_to_message: در صورت نیاز، پیام برای پاسخ دادن
    - kwargs: سایر پارامترها مثل parse_mode، disable_web_page_preview و غیره
    """
    try:
        if reply_to_message:
            # اگر پیام پاسخ داده شود، بررسی None بودن
            bot.send_message(
                chat_id, 
                text, 
                reply_to_message_id=getattr(reply_to_message, "message_id", None), 
                **kwargs
            )
        else:
            bot.send_message(chat_id, text, **kwargs)
    except AttributeError as e:
        # وقتی chat یا message None است
        print(f"⚠️ خطا در ارسال پیام (AttributeError): {e}")
    except Exception as e:
        # سایر خطاها
        print(f"⚠️ خطا در ارسال پیام: {e}")
