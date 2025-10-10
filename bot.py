import telebot
import requests
import time
import json
import os

# 📌 توکن خودت را از متغیر محیطی یا مستقیم وارد کن
TOKEN = os.getenv("BOT_TOKEN", "7850694628:AAEhddVGq-19haxezAy9PheqG1jkm8vcZ7w")

bot = telebot.TeleBot(TOKEN)

# 🧹 حذف خودکار Webhook در شروع
def delete_webhook():
    url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook"
    try:
        response = requests.get(url, timeout=10)
        result = response.json()
        if result.get("ok"):
            print("✅ Webhook removed successfully.")
        else:
            print("⚠️ Webhook remove failed:", result)
    except Exception as e:
        print("⚠️ Error deleting webhook:", e)

# 📁 بارگذاری داده‌ها
def load_data():
    if not os.path.exists("data.json"):
        return {"users": []}
    with open("data.json", "r") as f:
        return json.load(f)

# 💾 ذخیره داده‌ها
def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=2)

# 🧍‍♂️ افزودن کاربر جدید
def add_user(user_id):
    data = load_data()
    if user_id not in data["users"]:
        data["users"].append(user_id)
        save_data(data)
        print(f"👤 User {user_id} added.")
    else:
        print(f"ℹ️ User {user_id} already exists.")

# 🎯 هندلر برای /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    add_user(message.chat.id)
    bot.reply_to(message, "سلام 👋 ربات با موفقیت فعاله و آماده کاره ✅")

# 🔁 اجرای ربات
if __name__ == "__main__":
    print("🧹 Deleting webhook before starting polling...")
    delete_webhook()
    time.sleep(2)
    print("🤖 Bot is running and webhook removed successfully!")
    bot.infinity_polling()
