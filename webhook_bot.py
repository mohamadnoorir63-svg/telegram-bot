import os
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "🤖 Webhook bot is running!"

if __name__ == "__main__":
    print("✅ Webhook bot is starting...")  # پیام در ترمینال
    print("🌐 App URL:", os.getenv("APP_URL"))  # اختیاری: نمایش URL
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
