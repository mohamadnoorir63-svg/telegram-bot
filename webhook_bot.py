# =================== webhook_bot.py ===================
import os
import requests
from flask import Flask, request, jsonify

# ------------------ تنظیمات از محیط ------------------
TOKEN = os.getenv("TOKEN")
APP_URL = os.getenv("APP_URL")
GEOIP_KEY = os.getenv("GEOIP_KEY")

API = f"https://api.telegram.org/bot{TOKEN}"

# ------------------ اپ Flask ------------------
app = Flask(__name__)

# ------------------ توابع کمکی ------------------
def get_country(ip):
    """تشخیص کشور با استفاده از ipdata.co"""
    try:
        url = f"https://api.ipdata.co/{ip}?api-key={GEOIP_KEY}"
        r = requests.get(url, timeout=3)
        data = r.json()
        return data.get("country_code", "Unknown")
    except:
        return "Unknown"

def send_message(chat_id, text):
    """ارسال پیام به کاربر"""
    requests.post(f"{API}/sendMessage", json={
        "chat_id": chat_id,
        "text": text
    })

# ------------------ مسیر Webhook ------------------
@app.route(f"/{TOKEN}", methods=["POST"])
def bot_webhook():
    update = request.get_json()
    if not update:
        return jsonify({"ok": False})

    if "message" in update:
        msg = update["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")

        # گرفتن IP واقعی کاربر (Forwarded یا مستقیم)
        user_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        country_code = get_country(user_ip)

        # دسته‌بندی کشور
        if country_code in ["IR"]:
            speed = "🇮🇷 سرعت مخصوص ایران فعال شد!"
        elif country_code in ["AF"]:
            speed = "🇦🇫 خوش آمدید کاربر افغانستان!"
        elif country_code in ["DE", "FR", "NL", "SE", "UK", "IT", "ES", "NO", "FI", "PL"]:
            speed = "🇪🇺 کاربر اروپایی شناسایی شد!"
        else:
            speed = f"🌍 کشور شما شناسایی شد: {country_code}"

        # پاسخ سریع
        send_message(chat_id, speed)

    return jsonify({"ok": True})

# ------------------ تنظیم وب‌هوک ------------------
@app.route("/setwebhook")
def set_webhook():
    if not TOKEN or not APP_URL:
        return "⚠️ TOKEN یا APP_URL تنظیم نشده!", 400
    url = f"{APP_URL}/{TOKEN}"
    r = requests.get(f"{API}/setWebhook?url={url}")
    return r.json()

# ------------------ چک وضعیت وب‌هوک ------------------
@app.route("/checkwebhook")
def check_webhook():
    """وضعیت وب‌هوک را از تلگرام دریافت کن"""
    if not TOKEN:
        return "⚠️ TOKEN تنظیم نشده!", 400
    try:
        r = requests.get(f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo", timeout=5)
        data = r.json()
        return jsonify(data)
    except Exception as e:
        return f"⚠️ خطا در ارتباط با تلگرام: {e}", 500

# ------------------ اجرای اپ ------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
