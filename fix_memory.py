import json, os

SRC = "memory.json"
DST = "memory_fixed.json"

def ensure_list(x):
    # اگر مقدار None یا رشته بود، به لیست تبدیل کن
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]

def main():
    if not os.path.exists(SRC):
        print(f"❌ {SRC} پیدا نشد!")
        return

    with open(SRC, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"❌ خطا در خواندن JSON: {e}")
            return

    # اسکیمای استاندارد موردنیاز ربات:
    # {
    #   "data": { "جمله": ["پاسخ۱","پاسخ۲", ...] },
    #   "mode": "نرمال" | ...,
    #   "users": [123, ...]
    # }
    changed = 0
    data.setdefault("data", {})
    data.setdefault("mode", data.get("mode", "نرمال"))
    data.setdefault("users", data.get("users", []))

    fixed = {}
    for phrase, replies in data.get("data", {}).items():
        lst = ensure_list(replies)
        # حذف None/خالی‌ها و تبدیل به رشته
        lst = [str(x).strip() for x in lst if str(x).strip()]
        fixed[phrase] = lst
        if lst != replies:
            changed += 1

    data["data"] = fixed

    with open(DST, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ تمام شد! {changed} جمله اصلاح شد.")
    print(f"📄 فایل تمیز در: {DST}")

if __name__ == "__main__":
    main()
