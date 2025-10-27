import os, json

ADMIN_ID = int(os.getenv("ADMIN_ID", "7089376754"))
SUDO_FILE = "sudo_list.json"

# دیکشنری در حافظه (مثلاً {"7089": "Owner", "1234": "Sudo"})
SUDO_DATA = {}

def load_sudos():
    global SUDO_DATA
    if os.path.exists(SUDO_FILE):
        try:
            with open(SUDO_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    SUDO_DATA = {str(k): str(v) for k, v in data.items()}
                elif isinstance(data, list):
                    # سازگار با نسخه‌های قدیمی
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
    with open(SUDO_FILE, "w", encoding="utf-8") as f:
        json.dump(SUDO_DATA, f, ensure_ascii=False, indent=2)

def get_sudo_ids():
    return [int(i) for i in SUDO_DATA.keys()]

def is_sudo(uid: int):
    return str(uid) in SUDO_DATA

def add_sudo(uid: int, title="Sudo"):
    uid = str(uid)
    if uid in SUDO_DATA:
        return False
    SUDO_DATA[uid] = title
    save_sudos()
    return True

def del_sudo(uid: int):
    uid = str(uid)
    if uid == str(ADMIN_ID):
        return False  # مدیر اصلی حذف نمی‌شود
    if uid not in SUDO_DATA:
        return False
    del SUDO_DATA[uid]
    save_sudos()
    return True

def list_sudo_text():
    txt = "👑 <b>لیست سودوهای فعلی:</b>\n\n"
    for i, (sid, name) in enumerate(SUDO_DATA.items(), start=1):
        tag = " (Owner)" if int(sid) == ADMIN_ID else ""
        txt += f"{i}. <code>{sid}</code>{tag}\n"
    return txt

# بارگذاری اولیه
load_sudos()
