# ==============================
# app.py — Fast Heroku Webhook (Optimized Async)
# ==============================

import os
import asyncio
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Application
from bot import (
    register_handlers,
    init_files,
    start_userbot,
    notify_admin_on_startup,
    auto_backup,
    start_auto_brain_loop
)

# -------------------------
# 1) Config Vars
# -------------------------
TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # e.g., https://yourapp.herokuapp.com/webhook

if not TOKEN or not WEBHOOK_URL:
    raise ValueError("❌ BOT_TOKEN یا WEBHOOK_URL تنظیم نشده!")

# -------------------------
# 2) Init bot & application
# -------------------------
bot = Bot(token=TOKEN)
application = Application.builder().token(TOKEN).concurrent_updates(True).build()

# -------------------------
# 3) Initialize required files
# -------------------------
init_files()

# -------------------------
# 4) Register handlers
# -------------------------
register_handlers(application)

# -------------------------
# 5) Flask webhook server
# -------------------------
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "🤖 Bot is running!", 200

@app.route("/webhook", methods=["POST"])
async def webhook():
    """Receives updates from Telegram via webhook."""
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, bot)
        await application.update_queue.put(update)
    except Exception as e:
        print("❌ Webhook Error:", e)
        return "Error", 500
    return "OK", 200

# -------------------------
# 6) Startup tasks
# -------------------------
async def on_startup(app):
    """Run async startup tasks."""
    await notify_admin_on_startup(app)
    app.create_task(auto_backup(app.bot))
    app.create_task(start_auto_brain_loop(app.bot))
    app.create_task(start_userbot())  # Start userbot asynchronously
    print("🌙 Startup tasks scheduled ✅")

application.post_init = on_startup

# -------------------------
# 7) Run Flask + Telegram queue concurrently
# -------------------------
if __name__ == "__main__":
    print("🚀 Starting Fast Webhook Server...")

    loop = asyncio.get_event_loop()

    # Run telegram application in background (queue processor)
    loop.create_task(application.start())
    loop.create_task(application.updater.start_polling())  # Optional, can be removed if purely webhook

    # Run Flask app in executor to avoid blocking
    from threading import Thread

    def run_flask():
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

    Thread(target=run_flask, daemon=True).start()

    # Keep loop alive
    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        print("🛑 Shutting down...")
        loop.run_until_complete(application.stop())
        loop.close()
