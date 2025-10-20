import time
from collections import defaultdict, deque

# حافظه‌ی کوتاه‌مدت مکالمات کاربران
# هر کاربر فقط آخرین چند پیام خودش رو نگه می‌داره

class ContextMemory:
    def __init__(self, max_history=5, timeout=180):
        """
        max_history: چند پیام آخر هر کاربر نگه داشته بشه
        timeout: زمان انقضای حافظه برای هر کاربر (به ثانیه)
        """
        self.user_contexts = defaultdict(lambda: deque(maxlen=max_history))
        self.last_update = {}
        self.timeout = timeout

    def add_message(self, user_id: int, text: str):
        """افزودن پیام جدید به حافظه کاربر"""
        now = time.time()
        self.user_contexts[user_id].append(text.strip())
        self.last_update[user_id] = now

    def get_context(self, user_id: int):
        """برگرداندن کل مکالمه اخیر کاربر (در صورت معتبر بودن)"""
        now = time.time()
        if user_id not in self.last_update:
            return []
        if now - self.last_update[user_id] > self.timeout:
            # حافظه منقضی شده
            self.user_contexts[user_id].clear()
            return []
        return list(self.user_contexts[user_id])

    def clear_context(self, user_id: int):
        """پاک کردن حافظه موقتی کاربر"""
        if user_id in self.user_contexts:
            self.user_contexts[user_id].clear()
            self.last_update.pop(user_id, None)
