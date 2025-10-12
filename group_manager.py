import json
import os
from datetime import datetime

GROUP_FILE = "group_data.json"

# ======================= 📦 راه‌اندازی فایل گروه‌ها =======================

def init_group_file():
    """ایجاد فایل آمار گروه‌ها در صورت نبود"""
    if not os.path.exists(GROUP_FILE):
        with open(GROUP_FILE, "w", encoding="utf-8") as f:
            json.dump({"groups": {}}, f, ensure_ascii=False, indent=2)

# ======================= 📥 بارگذاری و ذخیره =======================

def load_groups():
    if not os.path.exists(GROUP_FILE):
        init_group_file()
    with open(GROUP_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_groups(data):
    with open(GROUP_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ======================= 🧩 ثبت فعالیت گروه =======================

def register_group_activity(group_id, user_id):
    """ثبت فعالیت کاربر در گروه"""
    data = load_groups()
    groups = data.get("groups", {})

    group_id = str(group_id)
    if group_id not in groups:
        groups[group_id] = {
            "title": f"Group_{group_id}",
            "members": [],
            "last_active": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    if user_id not in groups[group_id]["members"]:
        groups[group_id]["members"].append(user_id)

    groups[group_id]["last_active"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    data["groups"] = groups
    save_groups(data)

# ======================= 📊 آمار گروه =======================

def get_group_stats():
    """نمایش آمار کلی گروه‌ها و اعضا"""
    data = load_groups()
    groups = data.get("groups", {})

    total_groups = len(groups)
    total_users = sum(len(info.get("members", [])) for info in groups.values())

    return {
        "total_groups": total_groups,
        "total_users": total_users,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# ======================= 🧾 لیست گروه‌ها =======================

def list_groups():
    """لیست نام گروه‌ها و اعضای آنها"""
    data = load_groups()
    groups = data.get("groups", {})
    text = "📋 لیست گروه‌ها:\n\n"
    for gid, info in groups.items():
        title = info.get("title", f"Group_{gid}")
        members = len(info.get("members", []))
        last = info.get("last_active", "نامشخص")
        text += f"🏠 {title}\n👥 اعضا: {members}\n🕓 آخرین فعالیت: {last}\n\n"
    return text if groups else "هنوز در هیچ گروهی فعالیت نکرده‌ام 😅"
