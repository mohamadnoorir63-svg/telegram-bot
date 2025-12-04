import json
import os
from datetime import datetime

GROUP_FILE = "group_data.json"

# ======================= 📦 راه‌اندازی فایل گروه‌ها =======================
def init_group_file():
    """اگر فایل گروه وجود نداشت، ایجادش می‌کند"""
    if not os.path.exists(GROUP_FILE):
        with open(GROUP_FILE, "w", encoding="utf-8") as f:
            json.dump({"groups": {}}, f, ensure_ascii=False, indent=2)

# ======================= 📥 بارگذاری =======================
def load_groups():
    if not os.path.exists(GROUP_FILE):
        init_group_file()

    try:
        with open(GROUP_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        data = {"groups": {}}

    # اگر قدیمی بود و لیست بود → تبدیل کن
    if isinstance(data.get("groups"), list):
        new_dict = {}
        for g in data["groups"]:
            gid = str(g.get("id"))
            new_dict[gid] = g
        data["groups"] = new_dict
        save_groups(data)

    if "groups" not in data or not isinstance(data["groups"], dict):
        data["groups"] = {}

    return data

# ======================= 💾 ذخیره =======================
def save_groups(data):
    with open(GROUP_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ======================= 🧩 ثبت فعالیت گروه =======================
def register_group_activity(group_id, user_id, title="بدون‌نام"):
    data = load_groups()
    groups = data["groups"]

    gid = str(group_id)

    # اگر وجود ندارد، بساز
    if gid not in groups:
        groups[gid] = {
            "id": group_id,
            "title": title,
            "members": [],
            "last_active": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    # ثبت عضو
    if user_id not in groups[gid]["members"]:
        groups[gid]["members"].append(user_id)

    # بروزرسانی فعالیت
    groups[gid]["last_active"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    save_groups(data)

# ======================= 📊 آمار کلی =======================
def get_group_stats():
    data = load_groups()
    groups = data["groups"]

    total_groups = len(groups)
    total_members = sum(len(info.get("members", [])) for info in groups.values())

    return {
        "total_groups": total_groups,
        "total_members": total_members,
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# ======================= 📜 لیست کامل گروه‌ها =======================
def list_groups():
    data = load_groups()
    groups = data["groups"]

    if not groups:
        return "ℹ️ هنوز هیچ گروهی ثبت نشده."

    text = "📈 آمار کامل گروه‌ها:\n\n"

    for gid, info in groups.items():
        title = info.get("title", "بدون‌نام")
        members = len(info.get("members", []))
        last = info.get("last_active", "نامشخص")
        text += (
            f"🏠 گروه: {title}\n"
            f"🆔 {gid}\n"
            f"👥 اعضا: {members}\n"
            f"🕓 آخرین فعالیت: {last}\n"
            f"━━━━━━━━━━━━━━\n"
        )

    return text
