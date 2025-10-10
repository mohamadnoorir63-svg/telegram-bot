# -*- coding: utf-8 -*-
# Simple Persian Telegram Bot for Render (Web Service)
# - Long polling bot runs in a background thread
# - Flask web server binds to $PORT to satisfy Render's port check
# - Safe JSON storage for users list

import os, json, time, logging, threading
from datetime import datetime
from flask import Flask, jsonify
import telebot
from telebot import types

# ---------- Logging ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# ---------- Config ----------
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
SUDO_ID = int(os.environ.get("SUDO_ID", "0") or 0)
DATA_FILE = "data.json"

if not BOT_TOKEN:
    logging.error("BOT_TOKEN تنظیم نشده! از Environment Variables در Render اضافه‌اش کن.")
    raise SystemExit(1)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ---------- Safe JSON Storage ----------
_file_lock = threading.Lock()

def _base_data():
    return {"users": []}

def _load_data():
    # همیشه ساختار لازم را برمی‌گرداند
    if not os.path.exists(DATA_FILE):
        _save_data(_base_data())
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = _base_data()
    # تکمیل کلیدها در صورت ناقص بودن
    for k, v in _base_data().items():
        if k not in data:
            data[k] = v
    return data

def _save_data(data: dict):
    with _file_lock:
        tmp = DATA_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, DATA_FILE)

def add_user(user_id: int):
    with _file_lock:
        data = _load_data()
        if user_id not in data["users"]:
            data["users"].append(user_id)
            _save_data(data)

# ---------- Utils ----------
def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def is_sudo(uid: int) -> bool:
    return uid == SUDO_ID if SUDO_ID else False

# ---------- Handlers ----------
@bot.message_handler(commands=["start"])
def start_cmd(m):
    add_user(m.from_user.id)
    bot.reply_to(
        m,
        "سلام! 👋\nمن آنلاینم و کار می‌کنم.\n"
        "چند جملهٔ خودمونی که می‌تونی بفرستی:\n"
        "• سلام\n• آیدی\n• ساعت\n• وضعیت\n"
        "اگه چیزی نوشتی و جواب نداد، دوباره «سلام» بنویس 😉"
    )

@bot.message_handler(func=lambda m: (m.text or "").strip() != "")
def on_text(m):
    try:
        txt = (m.text or "").strip()
        add_user(m.from_user.id)

        low = txt.lower()
        # بدون اسلش و خودمونی
        if txt in ["آیدی", "ایدی", "id"]:
            bot.reply_to(m, f"🧾 آیدی شما: <code>{m.from_user.id}</code>")
            return

        if txt in ["ساعت", "زمان", "time"]:
            bot.reply_to(m, f"⏰ {now_str()}")
            return

        if txt in ["وضعیت", "status", "ربات", "bot"]:
            bot.reply_to(m, "✅ ربات آنلاینه و با سرعت در خدمتته! 🚀")
            return

        if "سلام" in txt or low in ["hi", "hello"]:
            first = (m.from_user.first_name or "دوست خوبم")
            bot.reply_to(m, f"سلام {first}! 😊\nچه خبر؟ اگه کمکی خواستی بنویس👌")
            return

        # جواب پیش‌فرض
        bot.reply_to(
            m,
            "من هستم 😉\n«آیدی»، «ساعت» یا «وضعیت» رو امتحان کن."
        )
    except Exception as e:
        logging.exception("text handler error: %s", e)

# (اختیاری) خوشامد به عضو جدید – اگر ربات در گروه ادمین باشد
@bot.message_handler(content_types=["new_chat_members"])
def welcome(m):
    try:
        u = m.new_chat_members[0]
        name = u.first_name or "دوست جدید"
        bot.send_message(
            m.chat.id,
            f"🎉 خوش اومدی {name}!\nامیدوارم اینجا بهت خوش بگذره 🌸"
        )
    except Exception as e:
        logging.exception("welcome error: %s", e)

# ---------- Polling thread ----------
def run_polling_forever():
    while True:
        try:
            logging.info("🔁 Bot polling شروع شد...")
            bot.infinity_polling(
                timeout=60,
                long_polling_timeout=40,
                skip_pending=True
            )
        except Exception as e:
            logging.exception("Polling crash: %s", e)
            time.sleep(5)  # تلاش مجدد

# ---------- Flask web server (for Render) ----------
app = Flask(__name__)

@app.get("/")
def home():
    return jsonify(ok=True, msg="Bot is running", time=now_str())

@app.get("/healthz")
def health():
    return "ok", 200

# ---------- Main ----------
if __name__ == "__main__":
    # راه‌اندازی ترد ربات
    t = threading.Thread(target=run_polling_forever, daemon=True)
    t.start()

    port = int(os.environ.get("PORT", "10000"))
    logging.info("🌐 Flask listening on 0.0.0.0:%s", port)
    logging.info("🤖 Bot online. اگر خطای 409 دیدی، مطمئن شو فقط یک سرویس فعاله.")
    app.run(host="0.0.0.0", port=port)
