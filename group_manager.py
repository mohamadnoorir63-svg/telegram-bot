import json
import os
from datetime import datetime

# ======================= 📁 مسیر فایل‌ها =======================
BASE_FOLDER = "data"
GROUP_FOLDER = os.path.join(BASE_FOLDER, "groups")
GROUP_FILE = os.path.join(GROUP_FOLDER, "group_data.json")
USER_FILE = os.path.join(BASE_FOLDER, "users.json")

# ======================= 📦 ایجاد پوشه‌های لازم =======================
def init_folders():
    if not os.path.exists(BASE_FOLDER):
        os.makedirs(BASE_FOLDER)

    if not os.path.exists(GROUP_FOLDER):
        os.makedirs(GROUP_FOLDER)

# ======================= 📂 ایجاد فایل‌ها =======================
def init_files():
    init_folders()

    if not os.path.exists(GROUP_FILE):
        with open(GROUP_FILE, "w", encoding="utf-8") as f:
            json.dump({"groups": {}}, f, ensure_ascii=False, indent=2)

    if not os.path.exists(USER_FILE):
        with open(USER_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)

# ======================= 📥 بارگذاری گروه‌ها =======================
def load_groups():
    init_files()

    try:
        with open(GROUP_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        data = {"groups": {}}

    if "groups" not in data or not isinstance(data["groups"], dict):
        data["groups"] = {}

    return data

# ======================= 💾 ذخیره گروه‌ها =======================
def save_groups(data):
    init_files()
    with open(GROUP_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ======================= 🧩 ثبت فعالیت گروه =======================
def register_group_activity(group_id, user_id, title="بدون‌نام"):
    data = load_groups()
    groups = data["groups"]

    gid = str(group_id)

    if gid not in groups:
        groups[gid] = {
            "id": group_id,
            "title": title,
            "members": [],
            "last_active": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    if user_id not in groups[gid]["members"]:
        groups[gid]["members"].append(user_id)

    groups[gid]["last_active"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    save_groups(data)

# ======================= 👤 ثبت کاربران پیوی =======================
def register_private_user(user):
    init_files()

    try:
        with open(USER_FILE, "r", encoding="utf-8") as f:
            users = json.load(f)
    except:
        users = []

    existed = any(u["id"] == user.id for u in users)

    if not existed:
        users.append({
            "id": user.id,
            "name": user.first_name,
            "username": user.username
        })

        with open(USER_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)

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
