import json
import re
import shutil
import os
from datetime import datetime
from telegram import Bot

# 🔹 تنظیمات محیطی
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
BOT_TOKEN = os.getenv("BOT_TOKEN")

# 📢 ارسال گزارش تعمیر به ADMIN
async def notify_admin(file_name, success=True, details=""):
    """ارسال گزارش تعمیر فایل برای ADMIN در تلگرام"""
    if not BOT_TOKEN or ADMIN_ID == 0:
        print("⚠️ BOT_TOKEN یا ADMIN_ID تنظیم نشده — ارسال پیام ممکن نیست.")
        return

    bot = Bot(token=BOT_TOKEN)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "✅ با موفقیت تعمیر شد" if success else "❌ با خطا مواجه شد"
    msg = (
        f"🧩 گزارش تعمیر فایل:\n\n"
        f"📁 فایل: {file_name}\n"
        f"📅 زمان: {now}\n"
        f"🔧 وضعیت: {status}\n"
    )
    if details:
        msg += f"📝 جزئیات:\n{details}"

    try:
        await bot.send_message(chat_id=ADMIN_ID, text=msg)
        print(f"📨 پیام تعمیر برای ADMIN ارسال شد: {file_name}")
    except Exception as e:
        print(f"⚠️ ارسال پیام تلگرام به ADMIN با خطا مواجه شد: {e}")


# 🧠 تعمیر خودکار JSON معیوب
async def fix_json(file_path):
    """
    🩺 تعمیر خودکار فایل JSON خراب با بک‌آپ و گزارش تلگرام.
    اگر فایل درست شد → True
    اگر نشد → False
    """
    if not os.path.exists(file_path):
        print(f"⚠️ فایل '{file_path}' وجود ندارد.")
        return False

    try:
        # تست باز کردن فایل
        with open(file_path, "r", encoding="utf-8") as f:
            json.load(f)
        print(f"✅ {file_path} سالم است، نیازی به تعمیر ندارد.")
        return True

    except json.JSONDecodeError as e:
        print(f"🚨 خطای JSON در {file_path}: {e}")
        details = str(e)

        # 🗂 ساخت نسخه پشتیبان از فایل خراب
        backup_path = file_path + ".bak"
        shutil.copy(file_path, backup_path)
        print(f"💾 نسخه پشتیبان ساخته شد: {backup_path}")

        # 📜 خواندن محتوا و تلاش برای اصلاح
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        fixed = content.strip()

        # رفع خطاهای رایج در ساختار JSON
        fixed = re.sub(r'^[^\{\[]+', '', fixed)
        fixed = re.sub(r'[^\}\]]+$', '', fixed)
        fixed = re.sub(r',\s*([\}\]])', r'\1', fixed)

        if not fixed.startswith("{") and not fixed.startswith("["):
            fixed = '{"data": {}, "users": []}'

        # بستن آکولادها و براکت‌های ناقص
        if fixed.count("{") > fixed.count("}"):
            fixed += "}" * (fixed.count("{") - fixed.count("}"))
        if fixed.count("[") > fixed.count("]"):
            fixed += "]" * (fixed.count("[") - fixed.count("]"))

        try:
            data = json.loads(fixed)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✅ فایل {file_path} تعمیر شد.")
            await notify_admin(file_path, success=True, details=details)
            return True

        except Exception as e2:
            print(f"❌ خطا در تعمیر {file_path}: {e2}")
            await notify_admin(file_path, success=False, details=str(e2))
            return False
