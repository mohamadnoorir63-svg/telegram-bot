import os
from memory_manager import load_data, save_data

# 📁 مسیر فایل پاسخ‌های سفارشی
REPLIES_FILE = "custom_replies.json"

def load_replies():
    """بارگذاری پاسخ‌های ذخیره‌شده"""
    if os.path.exists(REPLIES_FILE):
        return load_data(REPLIES_FILE)
    return {}

def save_replies(data):
    """ذخیره پاسخ‌ها در فایل JSON"""
    save_data(REPLIES_FILE, data)

def add_reply(keyword, msg):
    """ذخیره پاسخ جدید (متن یا مدیا)"""
    replies = load_replies()
    if msg.text:
        replies[keyword] = {"type": "text", "value": msg.text}
    elif msg.photo:
        replies[keyword] = {"type": "photo", "value": msg.photo[-1].file_id}
    elif msg.video:
        replies[keyword] = {"type": "video", "value": msg.video.file_id}
    elif msg.sticker:
        replies[keyword] = {"type": "sticker", "value": msg.sticker.file_id}
    elif msg.voice:
        replies[keyword] = {"type": "voice", "value": msg.voice.file_id}
    else:
        return False, "⚠️ نوع پیام پشتیبانی نمی‌شود (فقط متن، عکس، ویدیو، استیکر یا ویس)."
    save_replies(replies)
    return True, f"✅ پاسخ برای «{keyword}» ذخیره شد."

def delete_reply(keyword):
    """حذف پاسخ با کلمه‌کلیدی"""
    replies = load_replies()
    if keyword in replies:
        del replies[keyword]
        save_replies(replies)
        return f"🗑️ پاسخ برای «{keyword}» حذف شد."
    else:
        return "⚠️ هیچ پاسخی با این کلمه یافت نشد."

def list_replies():
    """نمایش تمام پاسخ‌های ذخیره‌شده"""
    replies = load_replies()
    if not replies:
        return "📂 هنوز هیچ پاسخ سفارشی ذخیره نشده 😅"
    msg = "📜 لیست پاسخ‌های سفارشی:\n\n"
    for k, v in replies.items():
        t = v.get("type", "text")
        icon = "💬" if t == "text" else "🖼️" if t == "photo" else "🎞️" if t == "video" else "🎙️" if t == "voice" else "🔘"
        msg += f"{icon} {k}\n"
    return msg

def get_reply(keyword):
    """گرفتن پاسخ با کلید"""
    replies = load_replies()
    return replies.get(keyword)
