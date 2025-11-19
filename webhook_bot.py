# =================== webhook_bot.py ===================
import os
import requests
from flask import Flask, request, jsonify
import io

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
    except Exception as e:
        print("GeoIP error:", e)
        return "Unknown"

def send_message(chat_id, text):
    try:
        requests.post(f"{API}/sendMessage", json={
            "chat_id": chat_id,
            "text": text
        })
    except Exception as e:
        print("Send message error:", e)

# ------------------ مسیر Webhook ------------------
@app.route(f"/{TOKEN}", methods=["POST"])
def bot_webhook():
    update = request.get_json()

    if not update:
        return jsonify({"ok": False})

    if "message" in update:
        msg = update["message"]
        chat_id = msg["chat"]["id"]

        # ------------------ گرفتن IP واقعی کاربر ------------------
        user_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        country_code = get_country(user_ip)

        # ------------------ دسته‌بندی کشور ------------------
        if country_code == "IR":
            speed = "🇮🇷 سرعت مخصوص ایران فعال شد!"
        elif country_code == "AF":
            speed = "🇦🇫 خوش آمدید کاربر افغانستان!"
        elif country_code in ["DE","FR","NL","SE","UK","IT","ES","NO","FI","PL"]:
            speed = "🇪🇺 کاربر اروپایی شناسایی شد!"
        else:
            speed = f"🌍 کشور شما شناسایی شد: {country_code}"

        send_message(chat_id, speed)

    return jsonify({"ok": True})

# ------------------ راه‌اندازی وب‌هوک ------------------
@app.route("/setwebhook")
def set_webhook():
    url = f"{APP_URL}/{TOKEN}"
    try:
        r = requests.get(f"{API}/setWebhook?url={url}")
        return r.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ------------------ شروع اپ ------------------
if __name__ == "__main__":
    print("✅ Webhook bot is starting...")
    print("🌐 App URL:", APP_URL)
    print("🔑 Token loaded:", "✅" if TOKEN else "❌")
    print("🗺 GeoIP key loaded:", "✅" if GEOIP_KEY else "❌")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
