import os, json

# 🧩 آیدی مدیر اصلی (می‌تونی تو Heroku هم با ENV تعریفش کنی)
ADMIN_ID = int(os.getenv("ADMIN_ID", "7089376754"))

# 📁 مسیر فایل سودوها
SUDO_FILE = "sudo_list.json"

# 🧠 داده‌های سودوها در حافظه
# ساختار: {"7089": "Owner", "1234": "Sudo"}
SUDO_DATA = {}


# ==================== 📂 توابع اصلی ====================

def load_sudos():
    """بارگذاری سودوها از فایل JSON"""
    global SUDO_DATA
    if os.path.exists(SUDO_FILE):
        try:
            with open(SUDO_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    SUDO_DATA = {str(k): str(v) for k, v in data.items()}
                elif isinstance(data, list):
                    # سازگار با نسخه‌های قدیمی‌تر
                    SUDO_DATA = {str(i): "Sudo" for i in data}
                else:
                    SUDO_DATA = {str(ADMIN_ID): "Owner"}
        except:
            SUDO_DATA = {str(ADMIN_ID): "Owner"}
    else:
        SUDO_DATA = {str(ADMIN_ID): "Owner"}
        save_sudos()
    return SUDO_DATA


def save_sudos():
    """ذخیره سودوها در فایل JSON"""
    with open(SUDO_FILE, "w", encoding="utf-8") as f:
        json.dump(SUDO_DATA, f, ensure_ascii=False, indent=2)


def get_sudo_ids():
    """برگرداندن لیست عددی از آیدی سودوها"""
    return [int(i) for i in SUDO_DATA.keys()]


def is_sudo(uid: int):
    """بررسی اینکه کاربر سودو هست یا نه"""
    return str(uid) in SUDO_DATA


def add_sudo(uid: int, title="Sudo"):
    """افزودن سودو جدید"""
    uid = str(uid)
    if uid in SUDO_DATA:
        return False
    SUDO_DATA[uid] = title
    save_sudos()
    return True


def del_sudo(uid: int):
    """حذف سودو"""
    uid = str(uid)
    if uid == str(ADMIN_ID):
        return False  # مدیر اصلی حذف نمی‌شود
    if uid not in SUDO_DATA:
        return False
    del SUDO_DATA[uid]
    save_sudos()
    return True


def list_sudo_text():
    """تولید متن نمایشی برای لیست سودوها"""
    txt = "👑 <b>لیست سودوهای فعلی:</b>\n\n"
    for i, (sid, name) in enumerate(SUDO_DATA.items(), start=1):
        tag = " (Owner)" if int(sid) == ADMIN_ID else ""
        txt += f"{i}. <code>{sid}</code>{tag}\n"
    return txt


# ==================== 🔄 بارگذاری اولیه ====================
load_sudos()


# ==================== 📦 خروجی‌های مجاز برای import ====================
__all__ = [
    "ADMIN_ID",
    "SUDO_DATA",
    "load_sudos",
    "save_sudos",
    "get_sudo_ids",
    "is_sudo",
    "add_sudo",
    "del_sudo",
    "list_sudo_text",
]
