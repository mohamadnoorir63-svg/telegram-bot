from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder
import os
import asyncio

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(TOKEN)
application = ApplicationBuilder().token(TOKEN).build()

# اضافه کردن handler هایی که میخوای Webhook سریع جواب بده
# مثلاً فقط start و متن ساده
from bot import start  # import handler اصلی از bot.py
application.add_handler(CommandHandler("start", start))

app = Flask(__name__)

@app.post("/")
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    application.update_queue.put_nowait(update)
    return "OK", 200
