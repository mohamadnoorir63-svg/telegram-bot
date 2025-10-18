import os, json, zipfile, random, asyncio, datetime
from telegram import Bot, InputFile

BASE = os.path.dirname(os.path.abspath(__file__))
OUT_JSON = os.path.join(BASE, "memory.json")
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
OUT_ZIP = os.path.join(BASE, f"khengol_brain_{timestamp}.zip")

# ===== حالت‌ها =====
MOODS = {
    "😎 شوخ": ["😂 خندیدم به حرفت!", "عه جدی گفتی؟ 😂", "تو خیلی باحالی 😎", "دارم از خنده می‌میرم 🤣", "خنگی ولی دوست‌داشتنی 😂"],
    "🫶 احساسی": ["دلم برات تنگ شده بود 😢", "تو همیشه خاصی برای من 💖", "چقدر حس خوبی دادی 😍", "آروم باش، من کنارت‌ام 💫", "ای کاش می‌تونستم بغلت کنم 🤗"],
    "😡 تند": ["حرف دهنتو بفهم 😤", "زیاد حرف نزن 😒", "مواظب لحنِت باش 😠", "داری رو اعصابم راه میری 😑", "خفه شو دیگه 😡"],
    "🧠 عادی": ["آره، متوجه شدم 🙂", "باشه، ادامه بده...", "جالبه 🤔", "منم همین فکرو می‌کردم 😌", "درسته ✅"],
}

BASE_PHRASES = [
    "سلام","خوبی","چیکار می‌کنی","دوستت دارم","چته","خفه شو","کجایی","برو بخواب","دلت برام تنگ شده","چی خوردی",
    "چرا ساکتی","صبح بخیر","شب بخیر","حوصلم سر رفته","می‌خوام بخندم","چرا ناراحتی","چقدر حرف می‌زنی","بیکاری",
    "دوست داری منو","چرا دیر جواب می‌دی","عاشقتم","چرا اخمو شدی","چی گفتی","من کیم","تو کی هستی","چرا اومدی",
    "حالت چطوره","می‌خوای حرف بزنیم","منو یادت هست","دوست داری سکوت کنیم","داری چیکار می‌کنی","از من بدت میاد",
]

def auto_learn_from_text(text: str):
    mood = random.choice(list(MOODS.keys()))
    patterns = [
        f"{text}؟ جالبه 🤔",
        f"{text}! عجب 😅",
        f"تو گفتی: {text}؟ منم همینه رو حس کردم {random.choice(['😏','😅','😂'])}",
        f"{text} رو گفتی؟ منم هم موافقم!",
        f"می‌دونی؟ {text} باعث شد لبخند بزنم 😄",
    ]
    return f"{random.choice(patterns)} ({mood})"

def build_brain(n=8000):  # ← سبک‌تر برای Heroku
    print("🧠 ساخت مغز خِنگول در حال اجراست...")
    phrases = {}
    for i in range(n):
        base = random.choice(BASE_PHRASES)
        mood, replies = random.choice(list(MOODS.items()))
        resp = random.choice(replies)
        if random.random() < 0.3:
            resp = auto_learn_from_text(base)
        phrases[f"{base}_{i}"] = [resp]

    # ذخیره فایل JSON
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump({"phrases": phrases}, f, ensure_ascii=False, indent=2)

    # ساخت ZIP سالم
    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(OUT_JSON, "memory.json")

    size = os.path.getsize(OUT_ZIP)
    print(f"✅ فایل ساخته شد ({size/1024/1024:.2f} MB): {OUT_ZIP}")
    return OUT_ZIP, size

async def send_zip(path):
    token = os.getenv("BOT_TOKEN")
    admin = int(os.getenv("ADMIN_ID", "7089376754"))
    bot = Bot(token=token)
    await bot.send_document(
        chat_id=admin,
        document=InputFile(path),
        caption=f"🧠 مغز خِنگول آماده‌ست!\n📦 ZIP: <code>{os.path.basename(path)}</code>\nاین فایل رو مستقیم برای ربات بفرست و /restore بزن ❤️",
        parse_mode="HTML"
    )
    print("📨 ارسال برای سودو انجام شد.")

if __name__ == "__main__":
    zip_path, size = build_brain()
    if size > 1000:
        asyncio.run(send_zip(zip_path))
    else:
        print("⚠️ فایل خراب یا ناقص است.")
