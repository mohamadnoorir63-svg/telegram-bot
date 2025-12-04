import os
import json
from datetime import datetime

# -----------------------------
# 📁 مسیر ذخیره‌سازی
# -----------------------------
DATA_DIR = "data"
GROUP_FILE = os.path.join(DATA_DIR, "groups.json")
USER_FILE = os.path.join(DATA_DIR, "users.json")

# -----------------------------
# 📌 ساخت فایل‌ها و پوشه‌ها
# -----------------------------
def init_storage():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    if not os.path.exists(GROUP_FILE):
        with open(GROUP_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)

    if not os.path.exists(USER_FILE):
        with open(USER_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)


# -----------------------------
# 👤 ثبت کاربر پیوی
# -----------------------------
def register_private_user(user):
    init_storage()

    try:
        with open(USER_FILE, "r", encoding="utf-8") as f:
            users = json.load(f)
    except:
        users = []

    # جلوگیری از ثبت تکراری
    if user.id not in [u["id"] for u in users]:
        users.append({
            "id": user.id,
            "name": user.first_name,
            "username": user.username,
        })

        with open(USER_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)


# -----------------------------
# 🏠 ثبت گروه + عضو
# -----------------------------
def register_group(chat, user):
    init_storage()

    try:
        with open(GROUP_FILE, "r", encoding="utf-8") as f:
            groups = json.load(f)
    except:
        groups = {}

    gid = str(chat.id)

    # اگر گروه جدید بود
    if gid not in groups:
        groups[gid] = {
            "id": chat.id,
            "title": chat.title or "بدون‌نام",
            "members": [],
            "last_active": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    # ثبت کاربر عضو
    if user.id not in groups[gid]["members"]:
        groups[gid]["members"].append(user.id)

    # بروزرسانی فعالیت
    groups[gid]["last_active"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ذخیره نهایی
    with open(GROUP_FILE, "w", encoding="utf-8") as f:
        json.dump(groups, f, ensure_ascii=False, indent=2)
