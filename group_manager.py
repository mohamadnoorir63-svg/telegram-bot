import json
import os
from datetime import datetime
from memory_manager import load_data, save_data

GROUP_FILE = "group_data.json"

# ======================= 📦 راه‌اندازی فایل گروه‌ها =======================
def init_group_file():
    """اگر فایل گروه وجود نداشت، ایجادش می‌کند"""
    if not os.path.exists(GROUP_FILE):
        with open(GROUP_FILE, "w", encoding="utf-8") as f:
            json.dump({"groups": []}, f, ensure_ascii=False, indent=2)

# ======================= 📥 بارگذاری و ذخیره =======================
def load_groups():
    """خواندن لیست گروه‌ها از فایل"""
    if not os.path.exists(GROUP_FILE):
        init_group_file()
    with open(GROUP_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            # اگر فایل خراب یا رشته بود، اصلاح شود
            if not isinstance(data, dict) or "groups" not in data:
                data = {"groups": []}
        except:
            data = {"groups": []}
    return data

def save_groups(data):
    """ذخیره داده گروه‌ها"""
    with open(GROUP_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ======================= 🧩 ثبت فعالیت گروه =======================
def register_group_activity(group_id, user_id, title="بدون‌نام"):
    """ثبت یا بروزرسانی اطلاعات یک گروه"""
    data = load_groups()
    groups = data.get("groups", [])

    # بررسی اینکه گروه قبلاً ثبت شده یا نه
    group = next((g for g in groups if g.get("id") == group_id), None)

    if not group:
        group = {
            "id": group_id,
            "title": title,
            "members": [],
            "last_active": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        groups.append(group)

    # افزودن کاربر جدید در صورت نبود
    if user_id not in group["members"]:
        group["members"].append(user_id)

    # بروزرسانی آخرین فعالیت
    group["last_active"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ذخیره در فایل
    data["groups"] = groups
    save_groups(data)

# ======================= 📊 آمار گروه =======================
def get_group_stats():
    """برگرداندن آمار کلی گروه‌ها"""
    data = load_groups()
    groups = data.get("groups", [])
    total_groups = len(groups)
    total_members = sum(len(g.get("members", [])) for g in groups)

    return {
        "total_groups": total_groups,
        "total_members": total_members,
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# ======================= 🧾 لیست گروه‌ها =======================
def list_groups():
    """لیست کامل گروه‌ها و اعضا"""
    data = load_groups()
    groups = data.get("groups", [])

    if not groups:
        return "ℹ️ هنوز هیچ گروهی ثبت نشده."

    text = "📈 آمار کامل گروه‌ها:\n\n"
    for g in groups:
        title = g.get("title", "بدون‌نام")
        members = len(g.get("members", []))
        last = g.get("last_active", "نامشخص")
        text += f"🏠 گروه: {title}\n👥 اعضا: {members}\n🕓 آخرین فعالیت: {last}\n\n"

    return text
