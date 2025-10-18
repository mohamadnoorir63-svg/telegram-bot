# make_and_send_brain.py
import os, json, zipfile, random, asyncio, datetime
from telegram import Bot, InputFile

# مسیر فایل‌ها
BASE = os.path.dirname(os.path.abspath(__file__))
OUT_JSON = os.path.join(BASE, "memory.json")

# 🧠 نام فایل ZIP با تاریخ جدید تا کش تلگرام نشود
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
OUT_ZIP  = os.path.join(BASE, f"khengol_brain_{timestamp}.zip")

# ================== حالت‌ها ==================
MOODS = {
    "😎 شوخ": ["😂 خندیدم به حرفت!", "عه جدی گفتی؟ 😂", "تو خیلی باحالی 😎", "دارم از خنده می‌میرم 🤣", "خنگی ولی دوست‌داشتنی 😂"],
    "🫶 احساسی": ["دلم برات تنگ شده بود 😢", "تو همیشه خاصی برای من 💖", "چقدر حس خوبی دادی 😍", "آروم باش، من کنارت‌ام 💫", "ای کاش می‌تونستم بغلت کنم 🤗"],
    "😡 تند": ["حرف دهنتو بفهم 😤", "زیاد حرف نزن 😒", "مواظب لحنِت باش 😠", "داری رو اعصابم راه میری 😑", "خفه شو دیگه 😡"],
    "🧠 عادی": ["آره، متوجه شدم 🙂", "باشه، ادامه بده...", "جالبه 🤔", "منم همین فکرو می‌کردم 😌", "درسته ✅"],
}

# ================== جمله‌های پایه ==================
BASE_PHRASES = [
    "سلام","خوبی","چیکار می‌کنی","دوستت دارم","چته","خفه شو","کجایی","برو بخواب","دلت برام تنگ شده","چی خوردی",
    "چرا ساکتی","صبح بخیر","شب بخیر","حوصلم سر رفته","می‌خوام بخندم","چرا ناراحتی","چقدر حرف می‌زنی","بیکاری",
    "دوست داری منو","چرا دیر جواب می‌دی","عاشقتم","چرا اخمو شدی","چی گفتی","من کیم","تو کی هستی","چرا اومدی",
    "حالت چطوره","می‌خوای حرف بزنیم","منو یادت هست","دوست داری سکوت کنیم","داری چیکار می‌کنی","از من بدت میاد",
]

# ================== یادگیری خودکار ==================
def auto_learn_from_text(text: str) -> str:
    mood = random.choice(list(MOODS.keys()))
    pattern = random.choice([
        f"{text}؟ جالبه 🤔",
        f"{text}! عجب 😅",
        f"تو گفتی: {text}؟ منم همینه رو حس کردم {random.choice(['😏','😅','😂'])}",
        f"{text} رو گفتی؟ منم هم موافقم!",
        f"می‌دونی؟ {text} باعث شد لبخند بزنم 😄",
    ])
    return f"{pattern} ({mood})"

# ================== ساخت مغز ==================
def build_brain(n=40000):
    print("🧠 در حال ساخت مغز خِنگول... کمی صبر کن 💪")
    phrases = {}
    for i in range(n):
        base = random.choice(BASE_PHRASES)
        mood, replies = random.choice(list(MOODS.items()))
        resp = random.choice(replies)
        if random.random() < 0.3:
            resp = auto_learn_from_text(base)
        phrases[f"{base}_{i}"] = [resp]

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump({"phrases": phrases}, f, ensure_ascii=False, indent=2)

    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.write(OUT_JSON, arcname="memory.json")

    size = os.path.getsize(OUT_ZIP)
    print(f"✅ ساخته شد: {OUT_ZIP} ({size/1024/1024:.2f} MB)")
    return OUT_ZIP, size

# ================== ارسال برای سودو ==================
async def send_zip(path: str):
    token = os.getenv("BOT_TOKEN")
    admin = int(os.getenv("ADMIN_ID", "7089376754"))
    if not token:
        raise RuntimeError("BOT_TOKEN در Config Vars تنظیم نشده.")
    bot = Bot(token=token)
    await bot.send_document(
        chat_id=admin,
        document=InputFile(path),
        caption=f"🧠 مغز خِنگول آماده‌ست!\n📦 فایل ZIP: <code>{os.path.basename(path)}</code>\nاین فایل رو مستقیم برای ربات بفرست و /restore بزن ❤️",
        parse_mode="HTML"
    )
    print("📨 فایل برای سودو ارسال شد.")

# ================== اجرای اصلی ==================
if __name__ == "__main__":
    zip_path, size = build_brain(n=40000)
    if size < 50000:
        print("⚠️ ZIP خیلی کوچک است؛ احتمالاً ساخت خراب شده.")
    else:
        asyncio.run(send_zip(zip_path))
