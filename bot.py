import os, json, random, asyncio, requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")

DATA_FILE = "memory.json"
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"learning": True, "talking": True, "memory": {}}, f, ensure_ascii=False, indent=2)

# -------------------- حافظه --------------------
def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# -------------------- تولید پاسخ هوشمند --------------------
def ai_reply(text):
    url = "https://api-inference.huggingface.co/models/HooshvareLab/bert-fa-base-uncased-clf-persiannews"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": text}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        if r.status_code == 200:
            return f"{text} 😉"
        else:
            return random.choice([
                "چه جالب گفتی 😄", "آره درسته 😁", "منم همین فکر رو کردم 🤔", 
                "عجب حرف باحالی زدی 😂", "در موردش فکر می‌کنم 😎"
            ])
    except Exception:
        return random.choice(["عه اینترنت قطع شده؟ 😅", "نمیشه الان جواب بدم 😐"])

# -------------------- پاسخ اصلی --------------------
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    data = load_data()
    memory = data["memory"]

    # ---- دستورات ----
    if text == "یادگیری روشن":
        data["learning"] = True
        save_data(data)
        return await update.message.reply_text("یادگیری روشن شد 🧠")
    if text == "یادگیری خاموش":
        data["learning"] = False
        save_data(data)
        return await update.message.reply_text("یادگیری خاموش شد 😴")
    if text == "حرف زدن خاموش":
        data["talking"] = False
        save_data(data)
        return await update.message.reply_text("خنگول دیگه ساکته 🤐")
    if text == "حرف زدن روشن":
        data["talking"] = True
        save_data(data)
        return await update.message.reply_text("خنگول دوباره حرف‌زن شد 😁")
    if text == "بازنشانی":
        data = {"learning": True, "talking": True, "memory": {}}
        save_data(data)
        return await update.message.reply_text("حافظه پاک شد ✅")
    if text == "وضعیت":
        status = f"یادگیری: {'روشن' if data['learning'] else 'خاموش'} | حرف زدن: {'روشن' if data['talking'] else 'خاموش'}"
        return await update.message.reply_text(status)
    if text.startswith("یاد بگیر:"):
        try:
            part = text.split("یاد بگیر:")[1].strip()
            if "،" in part:
                key, value = part.split("،", 1)
                key, value = key.strip(), value.strip()
                memory[key] = memory.get(key, []) + [value]
                save_data(data)
                return await update.message.reply_text(f"یاد گرفتم وقتی گفتن '{key}' بگم '{value}' 😎")
            else:
                return await update.message.reply_text("فرمت درست نیست. مثال: یاد بگیر: سلام، سلام خوش اومدی 🌸")
        except:
            return await update.message.reply_text("مشکلی در یادگیری پیش اومد 😅")

    # ---- پاسخ‌دهی ----
    if not data["talking"]:
        return
    if text in memory:
        response = random.choice(memory[text])
    else:
        response = ai_reply(text)
        if data["learning"]:
            memory[text] = [response]
            data["memory"] = memory
            save_data(data)
    await update.message.reply_text(response)

    # گاهی خودش حرف بزنه
    if random.random() < 0.1:
        await asyncio.sleep(random.randint(5, 15))
        talk = random.choice(["من هنوز اینجام 😁", "برو حرف بزن حوصله‌م سر رفت 😜", "هی منو یادت نره 😅"])
        await update.message.reply_text(talk)

# -------------------- شروع --------------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))
    print("🤖 خنگول نهایی در حال اجراست ...")
    app.run_polling()
