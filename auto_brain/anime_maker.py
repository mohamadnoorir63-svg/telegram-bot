import os
import time
import requests
from io import BytesIO
from telegram import Update
from telegram.ext import ContextTypes

HF_API_KEY = os.getenv("HF_API_KEY")

# چند مدل جایگزین؛ اگر اولی جواب نداد سراغ بعدی می‌ره
CANDIDATE_MODELS = [
    "akhaliq/AnimeGANv2",                 # اصلی
    "akhaliq/AnimeGANv2-Hayao",           # استایل هایائو
    "akhaliq/AnimeGANv2-Paprika",         # استایل پاپریکا
]

HEADERS = {
    "Authorization": f"Bearer {HF_API_KEY}",
    "Content-Type": "application/octet-stream",
}

async def anime_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # اگر عکس نیست
    if not update.message or not update.message.photo:
        return await update.message.reply_text("📸 لطفاً یک عکس بفرست تا کارتونی‌ش کنم!")

    # پیامِ «در حال پردازش»
    status_msg = await update.message.reply_text("🎨 در حال کارتونی کردن عکس... کمی صبر کن 💫")

    try:
        # دریافت بایت‌های عکس
        photo = update.message.photo[-1]
        tg_file = await photo.get_file()
        image_bytes = await tg_file.download_as_bytearray()

        # بررسی وجود API Key
        if not HF_API_KEY:
            await status_msg.edit_text("❌ کلید HF_API_KEY تنظیم نشده.")
            return

        # روی چند مدل تلاش می‌کنیم
        last_err_text = None
        for model_id in CANDIDATE_MODELS:
            api_url = f"https://api-inference.huggingface.co/models/{model_id}"

            # چند بار ریتـرای اگر مدل در حال لود بود
            for attempt in range(5):
                resp = requests.post(api_url, headers=HEADERS, data=image_bytes, timeout=60)

                # مدل در حال لود/صف (اغلب 503 یا 202)
                if resp.status_code in (503, 202):
                    # اگر برآورد زمان برگشت داده شد، کمی صبر کن
                    try:
                        info = resp.json()
                        wait_sec = int(info.get("estimated_time", 5))
                    except Exception:
                        wait_sec = 5
                    time.sleep(min(wait_sec, 10))
                    continue

                # احراز هویت اشتباه
                if resp.status_code == 401:
                    await status_msg.edit_text("🔒 کلید HuggingFace نامعتبر است (401).")
                    return

                # موفق: بایت تصویر
                if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image/"):
                    bio = BytesIO(resp.content)
                    bio.name = "anime.jpg"
                    await update.message.reply_photo(photo=bio, caption="✨ اینم نسخهٔ کارتونی عکست 😍")
                    await status_msg.delete()
                    return

                # ممکنه بدنه JSONِ خطا برگرده
                try:
                    err_json = resp.json()
                    last_err_text = err_json.get("error") or str(err_json)
                except Exception:
                    last_err_text = f"HTTP {resp.status_code}"

                # برای کدهای دیگه نیازی به ادامهٔ ریتـرای روی همین مدل نیست
                break

        # اگر به اینجا رسیدیم یعنی همهٔ مدل‌ها ناموفق بودند
        await status_msg.edit_text(
            "⚠️ خطا در پردازش عکس، لطفاً دوباره امتحان کن 🙏\n"
            f"جزئیات: {last_err_text or 'نامشخص'}"
        )

    except Exception as e:
        try:
            await status_msg.edit_text(f"❌ خطا در ارتباط با سرور: {e}")
        except:
            await update.message.reply_text(f"❌ خطا در ارتباط با سرور: {e}")
