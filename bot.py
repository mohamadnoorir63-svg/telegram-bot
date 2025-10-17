import asyncio
import os
import random
import zipfile
from datetime import datetime
from telegram import Update, InputFile
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from telegram.ext import CallbackQueryHandler
import aiofiles

# 📦 ماژول‌ها
from memory_manager import (
    init_files, load_data, save_data, learn, shadow_learn, get_reply,
    set_mode, get_stats, enhance_sentence, generate_sentence, list_phrases
)
from jokes_manager import save_joke, list_jokes
from fortune_manager import save_fortune, list_fortunes
from group_manager import register_group_activity, get_group_stats
from ai_learning import auto_learn_from_text
from smart_reply import detect_emotion, smart_response
from emotion_memory import remember_emotion, get_last_emotion, emotion_context_reply
from auto_brain.auto_brain import start_auto_brain_loop

# 🎯 تنظیمات پایه
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7089376754"))
init_files()

status = {
    "active": True,
    "learning": True,
    "welcome": True,
    "locked": False
}
# ======================= 💬 ریپلی مود گروهی و محدود به مدیران =======================
REPLY_FILE = "reply_status.json"

def load_reply_status():
    """خواندن وضعیت ریپلی مود برای تمام گروه‌ها"""
    import json, os
    if os.path.exists(REPLY_FILE):
        try:
            with open(REPLY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}  # ساختار داده: { "group_id": {"enabled": True/False} }


def save_reply_status(data):
    """ذخیره وضعیت ریپلی مود برای همه گروه‌ها"""
    import json
    with open(REPLY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


reply_status = load_reply_status()

