# ======================= 💎 Khenqol FontMaster 27.0 — Persian & English Hybrid Edition =======================
import random
import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# 🎨 تابع اصلی ساخت فونت
async def font_maker(update, context):
    text = update.message.text.strip()
    if not text.startswith("فونت "):
        return False

    name = text.replace("فونت", "").strip()
    if not name:
        return await update.message.reply_text("🖋 بعد از «فونت»، نام خودت رو بنویس تا فونت‌هات ساخته بشن.")

    # تشخیص فارسی یا انگلیسی
    is_english = bool(re.search(r"[a-zA-Z]", name))
    result = generate_english_fonts(name) if is_english else generate_persian_fonts(name)

    await update.message.reply_text(result["text"], parse_mode="HTML", reply_markup=result["keyboard"])
    return True


# ======================= 🏵 فونت فارسی =======================
def generate_persian_fonts(name):
    # طرح‌های خاص با خطوط تراز شده و یک‌خطی
    fonts = [
