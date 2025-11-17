from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes
import os
import logging

TOKEN = os.environ.get("TOKEN")

# -------------------------
# Flask Webhook
# -------------------------
app = Flask(__name__)

# -------------------------
# Logging
# -------------------------
logging.getLogger().setLevel(logging.WARNING)

# -------------------------
# ساخت Application
# -------------------------
application = ApplicationBuilder().token(TOKEN).build()

# -------------------------
# Route Webhook
# -------------------------
@app.route("/webhook", methods=["POST"])
async def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)
    await application.update_queue.put(update)  # ارسال به Application
    return "OK", 200
