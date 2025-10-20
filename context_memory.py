import time
from collections import defaultdict, deque

# 🧠 حافظه‌ی کوتاه‌مدت مکالمات کاربران
# هر کاربر فقط چند پیام آخر خودش رو نگه می‌داره و بعد از مدت زمان مشخص حذف میشه

class ContextMemory:
    def __init__(self, max_history: int = 5, timeout: int = 180):
        """
        max_history: تعداد پیام‌هایی که از هر کاربر نگهداری می‌شود.
        timeout: مدت زمان اعتبار حافظه برای هر کاربر (بر حسب ثانیه).
        """
        self.user_contexts = defaultdict(lambda: deque(maxlen=max_history))
        self.last_update = {}
        self.timeout = timeout

    def add_message(self, user_id: int, text: str):
        """افزودن پیام جدید به حافظه‌ی کاربر"""
        if not text:
            return
        now = time.time()
        self.user_contexts[user_id].append(text.strip())
        self.last_update[user_id] = now

    def get_context(self, user_id: int):
        """برگرداندن کل مکالمه‌ی اخیر کاربر (در صورت معتبر بودن)"""
        now = time.time()
        last_time = self.last_update.get(user_id)

        if not last_time:
            return []

        # اگر حافظه‌ی کاربر منقضی شده، پاکش کن
        if now - last_time > self.timeout:
            self.clear_context(user_id)
            return []

        # حافظه هنوز فعاله → زمان آخرین فعالیت رو تمدید کن
        self.last_update[user_id] = now
        return list(self.user_contexts[user_id])

    def clear_context(self, user_id: int):
        """پاک کردن حافظه‌ی موقت کاربر"""
        if user_id in self.user_contexts:
            self.user_contexts[user_id].clear()
            self.last_update.pop(user_id, None)

    def get_all_users(self):
        """برگرداندن لیست تمام کاربرانی که حافظه فعال دارند (برای دیباگ یا لاگ)"""
        return list(self.user_contexts.keys())
