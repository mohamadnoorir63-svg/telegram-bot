import os
import json
import datetime
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes
from openai import OpenAI

# 🔑 API از محیط سرور خوانده می‌شود
API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)

# 📁 مسیر فایل ذخیره کاربران
USERS_FILE = "ai_chat/ai_users.json"

# 👑 مدیر کل برای نامحدود بودن
ADMIN_ID = int(os.getenv("ADMIN_ID", "7089376754"))

# ======================= 📦 توابع کمکی =======================
def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(data):
    os.makedirs("ai_chat", exist_ok=True)
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def reset_if_new_day(user):
    """اگر تاریخ امروز نیست، امتیازها صفر شوند"""
    today = datetime.date.today().isoformat()
    if user.get("last_date") != today:
        user["count"] = 0
        user["last_date"] = today

# ======================= 🧠 پنل ChatGPT =======================
async def show_ai_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text = (
        "🤖 <b>گفتگوی هوش مصنوعی ChatGPT</b>\n\n"
        "💬 در این بخش می‌تونی با هوش مصنوعی حرفه‌ای گفتگو کنی.\n"
        "🧩 هر کاربر روزانه ۵ پیام رایگان داره.\n\n"
        "برای شروع روی دکمه زیر بزن 👇"
    )

    keyboard = [[InlineKeyboardButton("🚀 شروع گفتگو", callback_data="start_ai_chat")]]
    await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

# ======================= ▶️ شروع گفتگو =======================
async def start_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    users = load_users()
    user = users.get(str(user_id), {"count": 0, "last_date": ""})
    reset_if_new_day(user)
    users[str(user_id)] = user
    save_users(users)

    context.user_data["ai_chat_active"] = True

    await query.answer()
    await query.message.reply_text(
        "🧠 گفتگوی ChatGPT فعال شد!\n"
        "✍️ حالا هرچی می‌خوای بنویس تا هوش مصنوعی جواب بده.\n"
        "📊 پیام‌های باقی‌مانده‌ی امروز: ۵\n\n"
        "برای قطع گفتگو بنویس: <b>خاموش</b>",
        parse_mode="HTML"
    )

# ======================= 💬 چت با ChatGPT =======================
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # فقط وقتی گفتگوی ChatGPT فعاله
    if not context.user_data.get("ai_chat_active"):
        return

    users = load_users()
    user = users.get(str(user_id), {"count": 0, "last_date": ""})
    reset_if_new_day(user)

    # ✅ ادمین محدودیت نداره
    if user_id != ADMIN_ID and user["count"] >= 5:
        await update.message.reply_text("⚠️ امتیاز امروز شما تمام شد، فردا دوباره امتحان کنید 😅")
        return

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": text}]
        )
        reply_text = response.choices[0].message.content.strip()
    except Exception as e:
        reply_text = f"⚠️ خطا در ارتباط با ChatGPT:\n{e}"

    # شمارش پیام‌ها
    if user_id != ADMIN_ID:
        user["count"] += 1
        users[str(user_id)] = user
        save_users(users)

    remaining = 5 - user["count"]
    if remaining < 0:
        remaining = 0

    await update.message.reply_text(
        f"{reply_text}\n\n📊 پیام‌های باقی‌مانده‌ی امروز: {remaining}",
        parse_mode="HTML"
    )

# ======================= ⏹ توقف گفتگو =======================
async def stop_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("ai_chat_active"):
        return await update.message.reply_text("🤖 گفتگوی ChatGPT از قبل خاموش بود.")

    context.user_data["ai_chat_active"] = False
    await update.message.reply_text("🛑 گفتگوی ChatGPT متوقف شد. برای شروع دوباره، روی دکمه پنل بزن.")
