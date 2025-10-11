# -*- coding: utf-8 -*-
import os, json, random, asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

TOKEN = os.getenv("BOT_TOKEN")
SUDO_ID = int(os.getenv("SUDO_ID", "0"))
MEMORY_FILE = "memory.json"

# =============== مدل زبانی فارسی ===============
print("🤖 بارگذاری مدل هوش زبانی ...")
tokenizer = AutoTokenizer.from_pretrained("HooshvareLab/gpt2-fa")
model = AutoModelForCausalLM.from_pretrained("HooshvareLab/gpt2-fa")
model.eval()

# =============== حافظه ===============
if not os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "learning": True,
            "active": True,
            "mood": "happy",
            "chats": {},
            "custom_rules": {}
        }, f, ensure_ascii=False, indent=2)

def load_data():
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =============== تولید پاسخ هوشمند ===============
def generate_reply(prompt):
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=100)
    outputs = model.generate(**inputs, max_new_tokens=60, temperature=0.8, top_p=0.9, pad_token_id=tokenizer.eos_token_id)
    text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    text = text.replace(prompt, "").strip()
    if len(text) < 2:
        text = random.choice(["عه چه جالب 😄", "اینو خوب گفتی 😂", "باشه رفیق 😎"])
    return text

# =============== پاسخ‌دهی اصلی ===============
async def khengool(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    data = load_data()

    # حالت خاموش
    if not data.get("active", True):
        return

    # بررسی دستورات فارسی ساده
    msg_l = text.lower()
    chat_id = update.message.chat.id
    uid = update.message.from_user.id

    if msg_l == "یادگیری روشن":
        data["learning"] = True
        save_data(data)
        return await update.message.reply_text("🧠 یادگیری فعال شد.")
    if msg_l == "یادگیری خاموش":
        data["learning"] = False
        save_data(data)
        return await update.message.reply_text("😴 یادگیری غیرفعال شد.")
    if msg_l == "بازنشانی":
        data["chats"].clear()
        data["custom_rules"].clear()
        save_data(data)
        return await update.message.reply_text("♻️ حافظه‌ی خنگول پاک شد.")
    if msg_l == "وضعیت":
        status = "روشن ✅" if data.get("active", True) else "خاموش ❌"
        learning = "فعال 🧠" if data.get("learning", True) else "غیرفعال 😴"
        return await update.message.reply_text(f"وضعیت ربات: {status}\nوضعیت یادگیری: {learning}")
    if msg_l == "خنگول خاموش":
        data["active"] = False
        save_data(data)
        return await update.message.reply_text("🛑 خنگول خاموش شد.")
    if msg_l == "خنگول روشن":
        data["active"] = True
        save_data(data)
        return await update.message.reply_text("✅ خنگول روشن شد.")

    # یادگیری سفارشی
    if msg_l.startswith("یاد بگیر"):
        try:
            part = text.split("وقتی کسی گفت", 1)[1]
            trigger, replies = part.split("بگو", 1)
            trigger = trigger.strip()
            reply_list = [r.strip() for r in replies.split("\n") if r.strip()]
            if trigger and reply_list:
                data["custom_rules"][trigger] = reply_list
                save_data(data)
                return await update.message.reply_text(f"✅ یاد گرفتم وقتی کسی گفت «{trigger}» چی بگم 😎")
        except Exception:
            return await update.message.reply_text("❗فرمت درست: یاد بگیر وقتی کسی گفت سلام بگو:\nسلام رفیق 😎\nخوش اومدی ❤️")

    # پاسخ سفارشی
    for k, v in data["custom_rules"].items():
        if k in text:
            return await update.message.reply_text(random.choice(v))

    # فقط وقتی اسمش گفته بشه جواب بده
    if "خنگول" not in msg_l:
        if data.get("learning"):
            data["chats"][msg_l] = generate_reply(msg_l)
            if len(data["chats"]) > 200:
                data["chats"] = dict(list(data["chats"].items())[-200:])
            save_data(data)
        return

    # تولید پاسخ هوشمند
    mood_words = {"خوش": "happy", "غم": "sad", "عصب": "angry"}
    for word, mood in mood_words.items():
        if word in msg_l:
            data["mood"] = mood
            save_data(data)

    base_prompt = f"{text}\nخنگول:"
    reply = generate_reply(base_prompt)

    # ذخیره‌ی گفتگو
    if data.get("learning", True):
        data["chats"][msg_l] = reply
        if len(data["chats"]) > 200:
            data["chats"] = dict(list(data["chats"].items())[-200:])
        save_data(data)

    await update.message.reply_text(reply)

# =============== اجرا ===============
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, khengool))
    print("🤖 Khengool 2.0 Started ...")
    app.run_polling()
