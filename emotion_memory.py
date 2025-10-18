import json
import os
from datetime import datetime, timedelta

# 📁 مسیر فایل حافظه احساسات
EMOTION_FILE = "emotion_memory.json"


# ========================= ⚙️ آماده‌سازی =========================
def init_emotion_memory():
    """بررسی و ساخت فایل احساسات در صورت نبود"""
    if not os.path.exists(EMOTION_FILE):
        with open(EMOTION_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
        print("✅ فایل emotion_memory.json ساخته شد.")


# ========================= 💾 خواندن و ذخیره =========================
def load_emotions():
    try:
        with open(EMOTION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("⚠️ فایل احساسات خراب بود — بازنشانی شد.")
        save_emotions({})
        return {}
    except Exception as e:
        print(f"❌ خطا در بارگذاری emotion_memory.json: {e}")
        return {}


def save_emotions(data):
    try:
        with open(EMOTION_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ خطا در ذخیره احساسات: {e}")


# ========================= 💖 ثبت احساس جدید =========================
def remember_emotion(user_id: int, emotion: str):
    """ثبت احساس جدید برای هر کاربر"""
    data = load_emotions()
    now = datetime.now().isoformat()

    data[str(user_id)] = {
        "emotion": emotion,
        "last_update": now
    }

    save_emotions(data)


# ========================= 🔍 واکشی احساس قبلی =========================
def get_last_emotion(user_id: int) -> str:
    """برگرداندن آخرین احساس ذخیره‌شده کاربر"""
    data = load_emotions()
    info = data.get(str(user_id))

    if not info:
        return "neutral"

    try:
        last_time = datetime.fromisoformat(info.get("last_update", ""))
    except Exception:
        return "neutral"

    # اگر بیشتر از ۳۰ دقیقه گذشته باشه، احساس ریست میشه
    if datetime.now() - last_time > timedelta(minutes=30):
        return "neutral"

    return info.get("emotion", "neutral")


# ========================= ✨ بررسی و واکنش به تغییر احساس =========================
def emotion_context_reply(current_emotion: str, last_emotion: str) -> str:
    """ایجاد پاسخ بر اساس تغییر احساس کاربر"""
    if last_emotion == "sad" and current_emotion == "happy":
        return "😄 دیدی گفتم حالِت خوب میشه!"
    if last_emotion == "angry" and current_emotion == "neutral":
        return "😌 آروم شدی؟ خیلی خوبه!"
    if last_emotion == "happy" and current_emotion == "sad":
        return "😢 چی شد یهو ناراحت شدی؟"
    if last_emotion == "neutral" and current_emotion == "love":
        return "😍 اوه! یه حسی خاص پیدا کردی انگار!"
    if last_emotion == current_emotion:
        return None  # احساس تغییری نکرده

    return None
