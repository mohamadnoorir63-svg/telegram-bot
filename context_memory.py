# context_memory.py
import json
import os
from datetime import datetime

CONTEXT_FILE = "context_memory.json"

class ContextMemory:
    """مدیریت حافظه‌ی زمینه‌ای کاربران"""

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
                print(f"خطا در بارگذاری {self.file_path}، داده‌ها خالی شدند.")
                self.data = {}
        else:
            self.data = {}

    def save(self):
        """ذخیره داده‌ها در فایل JSON"""
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def set_context(self, user_id, context):
        """تنظیم حافظه‌ی زمینه‌ای برای یک کاربر"""
        self.data[str(user_id)] = {"context": context, "updated_at": str(datetime.now())}
        self.save()

    def get_context(self, user_id):
        """دریافت حافظه‌ی زمینه‌ای یک کاربر"""
        return self.data.get(str(user_id), {}).get("context")

    def clear_context(self, user_id):
        """پاکسازی حافظه‌ی زمینه‌ای یک کاربر"""
        if str(user_id) in self.data:
            del self.data[str(user_id)]
            self.save()
