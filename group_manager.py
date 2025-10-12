import json
from memory_manager import load_data, save_data

def register_group_activity(chat_id, user_id):
    """ثبت فعالیت کاربر در گروه برای آمار"""
    data = load_data("group_data.json")
    if "groups" not in data:
        data["groups"] = {}

    chat_id = str(chat_id)
    if chat_id not in data["groups"]:
        data["groups"][chat_id] = {"users": [], "messages": 0}

    if user_id not in data["groups"][chat_id]["users"]:
        data["groups"][chat_id]["users"].append(user_id)

    data["groups"][chat_id]["messages"] += 1
    save_data("group_data.json", data)

def get_group_stats():
    """برگرداندن اطلاعات گروه‌ها"""
    data = load_data("group_data.json").get("groups", {})
    return {
        "total_groups": len(data),
        "top_group": max(data.items(), key=lambda x: x[1]["messages"], default=(None, {}))[0]
    }
