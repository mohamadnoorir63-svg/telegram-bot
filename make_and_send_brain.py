# ================================================
# 🤖 خنگول مگابرین نهایی - نسخه پایدار مخصوص Heroku
# ================================================
import os, json, zipfile, random, asyncio
from telegram import Bot, InputFile

# مسیرها
BASE = os.path.dirname(os.path.abspath(__file__))
OUT_JSON = os.path.join(BASE, "memory.json")
OUT_ZIP = os.path.join(BASE, "khengol_brain_final.zip")

# ==================== 🎭 حالت‌های گفتاری ====================
MOODS = {
    "😎 شوخ": [
        "😂 خندیدم به حرفت!", "عه جدی گفتی؟ 😂", "تو خیلی باحالی 😎",
        "دارم از خنده می‌میرم 🤣", "خنگی ولی دوست‌داشتنی 😂"
    ],
    "🫶 احساسی": [
        "دلم برات تنگ شده بود 😢", "تو همیشه خاصی برای من 💖",
        "چقدر حس خوبی دادی 😍", "آروم باش، من کنارت‌ام 💫", "ای کاش می‌تونستم بغلت کنم 🤗"
    ],
    "😡 تند": [
        "حرف دهنتو بفهم 😤", "زیاد حرف نزن 😒", "مواظب لحنِت باش 😠",
        "داری رو اعصابم راه میری 😑", "خفه شو دیگه 😡"
    ],
    "🧠 عادی": [
        "آره، متوجه شدم 🙂", "باشه، ادامه بده...", "جالبه 🤔",
        "منم همین فکرو می‌کردم 😌", "درسته ✅"
    ]
}

# ==================== 🧠 تولید پاسخ‌ها ====================
BASE_PHRASES = [
    "سلام", "خوبی", "چیکار می‌کنی", "دوستت دارم", "چته", "خفه شو",
    "کجایی", "برو بخواب", "دلت برام تنگ شده", "چی خوردی", "چرا ساکتی",
    "صبح بخیر", "شب بخیر", "حوصلم سر رفته", "می‌خوام بخندم", "چرا ناراحتی",
    "چقدر حرف می‌زنی", "بیکاری", "دوست داری منو", "چرا دیر جواب می‌دی",
    "عاشقتم", "چرا اخمو شدی", "چی گفتی", "من کیم", "تو کی هستی",
    "چرا اومدی", "حالت چطوره", "می‌خوای حرف بزنیم", "منو یادت هست",
    "دوست داری سکوت کنیم", "داری چیکار می‌کنی", "از من بدت میاد"
]

def auto_reply(text: str):
    mood = random.choice(list(MOODS.keys()))
    tone = random.choice(MOODS[mood])
    extra = random.choice([
        f"{text}؟ جالبه 🤔", f"{text}! عجب 😅", f"تو گفتی: {text}؟ {tone}",
        f"{text} رو گفتی؟ منم همین حسو دارم 😏", f"می‌دونی؟ {text} باعث شد لبخند بزنم 😄"
    ])
    return f"{extra} ({mood})"

def build_brain(limit=25000):
    print("🧠 در حال ساخت مغز خنگول... لطفاً صبر کن ⏳")
    phrases = {}
    for i in range(limit):
        q = random.choice(BASE_PHRASES)
        a = auto_reply(q)
        phrases[f"{q}_{i}"] = [a]

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump({"phrases": phrases}, f, ensure_ascii=False)

    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(OUT_JSON, arcname="memory.json")

    size = os.path.getsize(OUT_ZIP)
    print(f"✅ ساخته شد ({size/1024/1024:.2f} MB) با {len(phrases):,} پاسخ")
    return OUT_ZIP, size

# ==================== 📤 ارسال خودکار برای سودو ====================
async def send_brain(path: str):
    token = os.getenv("BOT_TOKEN")
    admin = int(os.getenv("ADMIN_ID", "7089376754"))
    if not token:
        raise SystemExit("❌ BOT_TOKEN تنظیم نشده!")

    bot = Bot(token=token)
    await bot.send_document(
        chat_id=admin,
        document=InputFile(path),
        caption="🧠 مغز نهایی خِنگول ساخته شد و آماده بازیابی است ❤️\n\nبا دستور /restore آن را بازیابی کن.",
    )
    print("📤 ارسال موفق به سودو ✅")

# ==================== 🚀 اجرا ====================
if __name__ == "__main__":
    zip_path, size = build_brain()
    if size > 5000:
        asyncio.run(send_brain(zip_path))
    else:
        print("⚠️ ساخت فایل ناقص بود یا حجم خیلی کم است.")
