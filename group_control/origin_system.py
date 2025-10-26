import json, os, asyncio
from telegram import Update
from telegram.ext import ContextTypes

ORIGIN_FILE = "origins.json"
SUDO_IDS = [7089376754]

# 📂 بارگذاری و ذخیره‌سازی داده‌ها
def load_origins():
    if os.path.exists(ORIGIN_FILE):
        try:
            with open(ORIGIN_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_origins(data):
    with open(ORIGIN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

origins = load_origins()

# 👑 بررسی مدیر یا سودو بودن
async def is_admin_or_sudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    if user.id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        return member.status in ["administrator", "creator"]
    except:
        return False


# 🧹 حذف داده‌های گروه وقتی ربات از گروه خارج می‌شود
async def handle_bot_removed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id in origins:
        del origins[chat_id]
        save_origins(origins)
        print(f"🧹 داده‌های گروه {chat_id} حذف شد (ربات از گروه خارج شد)")


# ♻️ پاکسازی خودکار گروه‌های حذف‌شده یا غیرفعال
async def auto_clean_old_origins(context):
    print("🧭 شروع پاکسازی خودکار داده‌های قدیمی...")
    to_delete = []
    for chat_id in list(origins.keys()):
        try:
            chat = await context.bot.get_chat(chat_id)
            if chat.type not in ["group", "supergroup"]:
                to_delete.append(chat_id)
        except:
            to_delete.append(chat_id)

    for gid in to_delete:
        del origins[gid]

    if to_delete:
        save_origins(origins)
        print(f"🧹 {len(to_delete)} گروه غیرفعال حذف شدند: {', '.join(to_delete)}")
    else:
        print("✅ هیچ گروهی برای حذف وجود ندارد.")
