import os
import json
import datetime
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes
import openai
import httpx  # ✅ برای مدیریت خطاهای ارتباطی

# 🔑 کلید ChatGPT از محیط (در Heroku یا .env)
API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = API_KEY

# 📁 مسیر فایل کاربران برای محدودیت روزانه
USERS_FILE = "ai_chat/ai_users.json"

# 👑 مدیر کل (بدون محدودیت)
ADMIN_ID = int(os.getenv("ADMIN_ID", "7089376754"))

# ======================= 📦 توابع کمکی =======================
def load_users():
    """بارگذاری کاربران از فایل JSON"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_users(data):
    """ذخیره کاربران در فایل"""
    os.makedirs("ai_chat", exist_ok=True)
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def reset_if_new_day(user):
    """اگر تاریخ تغییر کرده، شمارش روزانه صفر شود"""
    today = datetime.date.today().isoformat()
    if user.get("last_date") != today:
        user["count"] = 0
        user["last_date"] = today

# ======================= 🧠 پنل ChatGPT =======================
async def show_ai_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش پنل ChatGPT با دکمه شروع گفتگو"""
    query = update.callback_query
    await query.answer()

    text = (
        "🤖 <b>گفتگوی هوش مصنوعی ChatGPT</b>\n\n"
        "💬 در این بخش می‌تونی با هوش مصنوعی پیشرفته چت کنی.\n"
        "🧩 هر کاربر روزانه تا ۵ پیام رایگان داره.\n\n"
        "برای شروع گفتگو روی دکمه زیر بزن 👇"
    )

    keyboard = [[InlineKeyboardButton("🚀 شروع گفتگو", callback_data="start_ai_chat")]]
    await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

# ======================= ▶️ شروع گفتگو =======================
async def start_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فعال‌سازی حالت گفتگو با ChatGPT"""
    query = update.callback_query
    user_id = query.from_user.id

    users = load_users()
    user = users.get(str(user_id), {"count": 0, "last_date": ""})
    reset_if_new_day(user)
    users[str(user_id)] = user
    save_users(users)

    context.user_data["ai_chat_active"] = True
    context.user_data["ai_history"] = [  # 🧠 شروع تاریخچه گفتگو
        {"role": "system", "content": "You are a helpful AI assistant named Khengool."}
    ]

    await query.answer()
    await query.message.reply_text(
        "🧠 گفتگوی ChatGPT فعال شد!\n"
        "✍️ حالا هرچی خواستی بنویس تا پاسخ بدم 😄\n"
        "📊 پیام‌های رایگان امروز: ۵\n\n"
        "برای خاموش کردن بنویس: <b>خاموش</b>",
        parse_mode="HTML"
    )

# ======================= 💬 چت با ChatGPT =======================
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش پیام‌های کاربر هنگام فعال بودن ChatGPT با حافظه مکالمه"""
    chat_type = update.message.chat.type
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # 🚫 فقط در چت خصوصی فعال است
    if chat_type != "private":
        return

    if not context.user_data.get("ai_chat_active"):
        return

    users = load_users()
    user = users.get(str(user_id), {"count": 0, "last_date": ""})
    reset_if_new_day(user)

    # محدودیت برای کاربران عادی
    if user_id != ADMIN_ID and user["count"] >= 5:
        await update.message.reply_text("⚠️ امتیاز امروزت تموم شد، فردا دوباره امتحان کن 😅")
        return

    # 🧠 ایجاد تاریخچه برای کاربر جدید
    if "ai_history" not in context.user_data:
        context.user_data["ai_history"] = [
            {"role": "system", "content": "You are a helpful AI assistant named Khengool."}
        ]

    # افزودن پیام کاربر به تاریخچه
    context.user_data["ai_history"].append({"role": "user", "content": text})

    # 🧩 درخواست به API ChatGPT با مدیریت خطا
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=context.user_data["ai_history"],
            timeout=30,  # جلوگیری از ReadError
        )
        reply_text = response.choices[0].message["content"].strip()

        # افزودن پاسخ مدل به تاریخچه
        context.user_data["ai_history"].append({"role": "assistant", "content": reply_text})

    except httpx.ReadError:
        reply_text = "⚠️ خطا در خواندن پاسخ از سرور ChatGPT!\nلطفاً چند لحظه بعد دوباره امتحان کن 🤖"

    except openai.error.APIConnectionError:
        reply_text = "🌐 اتصال به سرور ChatGPT برقرار نشد.\nممکنه اینترنت یا سرور موقتاً مشکل داشته باشه."

    except openai.error.Timeout:
        reply_text = "⏳ درخواست به ChatGPT بیش از حد طول کشید. لطفاً دوباره امتحان کن."

    except Exception as e:
        reply_text = f"⚠️ خطا در ارتباط با ChatGPT:\n{e}"

    # افزایش شمارش پیام‌ها
    if user_id != ADMIN_ID:
        user["count"] += 1
        users[str(user_id)] = user
        save_users(users)

    remaining = max(0, 5 - user["count"])

    await update.message.reply_text(
        f"{reply_text}\n\n📊 پیام‌های باقی‌مانده‌ی امروز: {remaining}",
        parse_mode="HTML"
    )

# ======================= ⏹ توقف گفتگو =======================
async def stop_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """غیرفعال‌سازی ChatGPT"""
    if not context.user_data.get("ai_chat_active"):
        return await update.message.reply_text("🤖 گفتگوی ChatGPT از قبل خاموش بود.")

    context.user_data["ai_chat_active"] = False
    context.user_data.pop("ai_history", None)  # 🧹 پاک کردن تاریخچه مکالمه
    await update.message.reply_text("🛑 گفتگوی ChatGPT متوقف شد. برای شروع دوباره، از پنل ChatGPT استفاده کن.")
