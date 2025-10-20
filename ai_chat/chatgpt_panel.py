import os
import json
import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import openai

# بارگذاری کلید API از متغیر محیطی Heroku
openai.api_key = os.getenv("OPENAI_API_KEY")

DATA_FILE = "user_points.json"

# اگر فایل وجود نداشت، بسازش
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

# لود کردن امتیاز کاربران
def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

# ذخیره‌ی امتیاز کاربران
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# چک کردن و آپدیت امتیاز روزانه
def reset_daily_points(user_id):
    data = load_data()
    today = datetime.date.today().isoformat()
    if str(user_id) not in data or data[str(user_id)]["date"] != today:
        data[str(user_id)] = {"points": 5, "date": today}
        save_data(data)

# دریافت تعداد امتیاز
def get_points(user_id):
    data = load_data()
    return data.get(str(user_id), {"points": 5}).get("points", 0)

# تغییر امتیاز
def update_points(user_id, amount):
    data = load_data()
    today = datetime.date.today().isoformat()
    if str(user_id) not in data:
        data[str(user_id)] = {"points": 5, "date": today}
    data[str(user_id)]["points"] += amount
    data[str(user_id)]["date"] = today
    save_data(data)

# دستور شروع
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reset_daily_points(update.effective_user.id)
    await update.message.reply_text("👋 سلام! خوش اومدی به چت هوش مصنوعی.\nتو امروز ۵ پیام رایگان داری 🤖")

# دستور اهدای امتیاز توسط ادمین
ADMIN_ID =  7089376754 # 👈 آیدی عددی خودت رو اینجا بزار

async def give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط ادمین می‌تونه امتیاز بده.")
    
    if len(context.args) < 2:
        return await update.message.reply_text("مثال: /give <user_id> <amount>")
    
    user_id = context.args[0]
    amount = int(context.args[1])
    update_points(user_id, amount)
    await update.message.reply_text(f"✅ به کاربر {user_id} {amount} امتیاز اضافه شد.")

# چت هوش مصنوعی
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    reset_daily_points(user_id)
    points = get_points(user_id)

    if points <= 0:
        return await update.message.reply_text("⚠️ امتیاز شما برای امروز تمام شد!\nفردا دوباره امتحان کنید 🌅")

    user_msg = update.message.text
    await update.message.chat.send_action("typing")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_msg}],
            max_tokens=200
        )
        reply = response.choices[0].message["content"]
        update_points(user_id, -1)
        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در ارتباط با API:\n{e}")

# اجرای برنامه
def main():
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("give", give))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.run_polling()

if __name__ == "__main__":
    main()
