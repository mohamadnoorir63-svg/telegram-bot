# -*- coding: utf-8 -*-
import os, json, random, asyncio, aiohttp
from gtts import gTTS
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
MEMORY_FILE = "memory.json"

# ===================== حافظه =====================
if not os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump({"learning": True, "mood": "happy", "chats": {}}, f, ensure_ascii=False, indent=2)

def load_data():
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)# ===================== تولید صدا =====================
def make_voice(text, filename="voice.ogg"):
    """تبدیل متن به صدا با gTTS"""
    try:
        tts = gTTS(text=text, lang="fa")
        tts.save(filename)
        return filename
    except Exception as e:
        print("خطا در ساخت صدا:", e)
        return None

# ===================== مودها =====================
MOODS = {
    "happy": [
        "عه سلام! 😄", "چه باحال گفتی 😂", "منم همینو می‌خواستم بگم 😆",
        "آره دیگه زندگی همینه 😎", "خوشحالم ببینمت 😍"
    ],
    "sad": [
        "اوه حوصله ندارم 😔", "غم دارم امروز 😢", "بیخیال حرف نزن الان 😕",
        "دلم گرفته یه کم 😞"
    ],
    "angry": [
        "ولم کن اعصاب ندارم 😡", "باز شروع شد؟ 😤", "می‌خوای دعوا کنیم؟ 😠",
        "چی گفتی؟ حواست باشه! 😒"
    ]
}# ===================== پاسخ هوش مصنوعی =====================
async def ask_huggingface(prompt):
    """ارسال سوال به Hugging Face API"""
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://api-inference.huggingface.co/models/gpt2"
            headers = {"Authorization": f"Bearer {HF_TOKEN}"}
            payload = {"inputs": prompt}

            async with session.post(url, headers=headers, json=payload, timeout=60) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        return data[0].get("generated_text", "").strip()
                    elif isinstance(data, dict):
                        return data.get("generated_text", "").strip()
                else:
                    print("HF Error:", await resp.text())
                    return None
    except Exception as e:
        print("خطا در ارتباط با Hugging Face:", e)
        return None

# ===================== تولید پاسخ =====================
async def generate_reply(user_text):
    data = load_data()
    chats = data.get("chats", {})
    mood = data.get("mood", "happy")

    # اگر قبلاً یاد گرفته
    if user_text in chats and len(chats[user_text]) > 0:
        return random.choice(chats[user_text])

    # اگر بلد نیست → از هوش مصنوعی بپرس
    ai_answer = await ask_huggingface(user_text)
    if ai_answer:
        # پاسخ رو ذخیره کن برای دفعات بعد
        if data.get("learning", True):
            chats.setdefault(user_text, []).append(ai_answer)
            data["chats"] = chats
            save_data(data)
        return ai_answer

    # اگر هوش مصنوعی هم جواب نداد
    return random.choice(MOODS[mood])# ===================== پاسخ خنگول =====================
async def khengool_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    if not text:
        return

    data = load_data()
    learning = data.get("learning", True)

    # فقط وقتی اسم خنگول گفته بشه فعال شو (در گروه‌ها)
    keywords = ["خنگول", "خنگی", "خنگول جون", "khengool"]
    if not any(k in text for k in keywords) and update.message.chat.type != "private":
        return

    # پاک کردن اسم از جمله
    for k in keywords:
        text = text.replace(k, "").strip()

    # تولید پاسخ
    reply = await generate_reply(text)
    await update.message.reply_text(reply)

    # ساخت و ارسال صدا
    voice_path = make_voice(reply)
    if voice_path:
        with open(voice_path, "rb") as v:
            await update.message.reply_voice(v)

    # گاهی خودش وسط حرف می‌پره 😆
    if random.random() < 0.12:
        await asyncio.sleep(random.randint(2, 6))
        say = random.choice([
            "من هنوز اینجام 😁", 
            "حوصله‌م سر رفت 😜", 
            "هی منو صدا نزن، خسته شدم 😅",
            "می‌دونی امروز دلم چی می‌خواد؟ یه بستنی 🍦"
        ])
        await update.message.reply_text(say)
        voice_path = make_voice(say)
        if voice_path:
            with open(voice_path, "rb") as v:
                await update.message.reply_voice(v)

# ===================== کنترل مود =====================
async def set_mood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not context.args:
        await update.message.reply_text(f"مود فعلی: {data['mood']}")
        return

    mood = context.args[0].lower()
    if mood not in MOODS:
        await update.message.reply_text("مودهای موجود: happy / sad / angry")
        return

    data["mood"] = mood
    save_data(data)
    await update.message.reply_text(f"مود خنگول تغییر کرد به {mood} 😎")

# ===================== یادگیری روشن / خاموش =====================
async def toggle_learning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    data["learning"] = not data.get("learning", True)
    save_data(data)
    status = "روشن 😁" if data["learning"] else "خاموش 😴"
    await update.message.reply_text(f"یادگیری الان {status} است.")# ===================== شروع ربات =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "سلام من خنگولم 🤪 بیا باهام حرف بزن!"
    await update.message.reply_text(msg)
    voice_path = make_voice(msg)
    if voice_path:
        with open(voice_path, "rb") as v:
            await update.message.reply_voice(v)

# ===================== وضعیت خنگول =====================
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    mood = data.get("mood", "happy")
    learning = "روشن" if data.get("learning", True) else "خاموش"
    total = len(data.get("chats", {}))
    msg = f"📊 وضعیت خنگول:\n\nمود: {mood}\nیادگیری: {learning}\nتعداد جملات یادگرفته‌شده: {total}"
    await update.message.reply_text(msg)

# ===================== ریست حافظه =====================
async def reset_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump({"learning": True, "mood": "happy", "chats": {}}, f, ensure_ascii=False, indent=2)
    await update.message.reply_text("🧠 حافظه خنگول پاک شد! حالا مثل روز اوله 😅")

# ===================== اجرای ربات =====================
if __name__ == "__main__":
    print("🤖 خنگول نهایی در حال اجراست ...")
    app = ApplicationBuilder().token(TOKEN).build()

    # دستورها
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mood", set_mood))
    app.add_handler(CommandHandler("learn", toggle_learning))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("reset", reset_memory))

    # پیام‌ها
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, khengool_reply))

    app.run_polling()
