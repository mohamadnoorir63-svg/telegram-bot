# context_memory.py
import json
import os
from datetime import datetime

CONTEXT_FILE = "context_memory.json"

class ContextMemory:
    """مدیریت حافظه‌ی زمینه‌ای کاربران و پیام‌ها"""

    def __init__(self, file_path=CONTEXT_FILE):
        self.file_path = file_path
        self.data = {}
        self.load()

    def load(self):
        """بارگذاری داده‌ها از فایل JSON"""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except json.JSONDecodeError:
                print(f"خطا در بارگذاری {self.file_path}, داده‌ها خالی شدند.")
                self.data = {}
        else:
            self.data = {}

    def save(self):
        """ذخیره داده‌ها در فایل JSON"""
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    # ===== حافظه زمینه‌ای ساده =====
    def set_context(self, user_id, context):
        self.data[str(user_id)] = {"context": context, "updated_at": str(datetime.now())}
        self.save()

    def get_context(self, user_id):
        return self.data.get(str(user_id), {}).get("context")

    def clear_context(self, user_id):
        if str(user_id) in self.data:
            del self.data[str(user_id)]
            self.save()

    # ===== مدیریت پیام‌ها =====
    def add_message(self, user_id, message):
        """اضافه کردن یک پیام به حافظه زمینه‌ای کاربر"""
        uid = str(user_id)
        if uid not in self.data:
            self.data[uid] = {"messages": [], "updated_at": str(datetime.now())}
        if "messages" not in self.data[uid]:
            self.data[uid]["messages"] = []
        self.data[uid]["messages"].append({"text": message, "timestamp": str(datetime.now())})
        self.data[uid]["updated_at"] = str(datetime.now())
        self.save()

    def get_messages(self, user_id, limit=10):
        """دریافت آخرین پیام‌ها"""
        uid = str(user_id)
        msgs = self.data.get(uid, {}).get("messages", [])
        return msgs[-limit:] if msgs else []

    def clear_messages(self, user_id):
        """پاکسازی همه پیام‌ها"""
        uid = str(user_id)
        if uid in self.data and "messages" in self.data[uid]:
            self.data[uid]["messages"] = []
            self.save()
