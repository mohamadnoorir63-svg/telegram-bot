# ==========================================================
# 🔰 Group System Module (for Persian Smart Bot)
# ==========================================================
import os, json, re, asyncio
from datetime import datetime, timedelta, time, timezone
from telegram import Update, ChatPermissions, MessageEntity
from telegram.ext import ContextTypes
from telegram.error import BadRequest, RetryAfter

# ─────────────────────────────── ذخیره‌سازی ───────────────────────────────
GROUP_CTRL_FILE = "group_control.json"
ALIASES_FILE = "aliases.json"
FILTER_FILE = "filters.json"
ORIGINS_FILE = "origins.json"
NICKS_FILE = "nicks.json"
BACKUP_DIR = "backups"

if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

def _load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return default

def _save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ خطا در ذخیره {path}: {e}")

# داده‌های اصلی
group_data = _load_json(GROUP_CTRL_FILE, {})
filters_db = _load_json(FILTER_FILE, {})
ALIASES = _load_json(ALIASES_FILE, {})
origins_db = _load_json(ORIGINS_FILE, {})
nicks_db = _load_json(NICKS_FILE, {})

# ─────────────────────────────── سودو ───────────────────────────────
SUDO_FILE = "sudos.json"
def _load_sudos():
    if os.path.exists(SUDO_FILE):
        with open(SUDO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []
SUDO_IDS = _load_sudos() or [7089376754]

# ─────────────────────────────── ابزارها ───────────────────────────────
async def _is_admin_or_sudo_uid(context, chat_id: int, user_id: int) -> bool:
    if user_id in SUDO_IDS:
        return True
    admins = group_data.get(str(chat_id), {}).get("admins", [])
    if str(user_id) in admins:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except:
        return False

# ─────────────────────────────── قفل‌ها (نمونه) ───────────────────────────────
LOCK_TYPES = {
    "links": "ارسال لینک",
    "photos": "ارسال عکس",
    "videos": "ارسال ویدیو",
}

def _locks_get(chat_id: int) -> dict:
    return group_data.get(str(chat_id), {}).get("locks", {})

def _locks_set(chat_id: int, key: str, status: bool):
    cid = str(chat_id)
    g = group_data.get(cid, {})
    locks = g.get("locks", {})
    locks[key] = status
    g["locks"] = locks
    group_data[cid] = g
    _save_json(GROUP_CTRL_FILE, group_data)

async def handle_lock(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
    if not await _is_admin_or_sudo_uid(context, update.effective_chat.id, update.effective_user.id):
        return await update.message.reply_text("🚫 فقط مدیر یا سودو می‌تواند قفل کند.")
    _locks_set(update.effective_chat.id, key, True)
    await update.message.reply_text(f"🔒 قفل {LOCK_TYPES[key]} فعال شد.")

async def handle_unlock(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
    if not await _is_admin_or_sudo_uid(context, update.effective_chat.id, update.effective_user.id):
        return await update.message.reply_text("🚫 فقط مدیر یا سودو می‌تواند باز کند.")
    _locks_set(update.effective_chat.id, key, False)
    await update.message.reply_text(f"🔓 قفل {LOCK_TYPES[key]} باز شد.")

# ─────────────────────────────── بررسی پیام‌ها ───────────────────────────────
async def check_message_locks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    if not msg or not chat or not user:
        return

    if await _is_admin_or_sudo_uid(context, chat.id, user.id):
        return

    locks = _locks_get(chat.id)
    text = msg.text or msg.caption or ""

    async def _del(reason):
        try:
            await msg.delete()
            warn = await context.bot.send_message(chat.id, f"🚫 {reason} توسط {user.first_name} حذف شد.")
            await asyncio.sleep(5)
            await warn.delete()
        except:
            pass

    if locks.get("links") and ("http" in text or "t.me" in text):
        return await _del("ارسال لینک")

    if locks.get("photos") and msg.photo:
        return await _del("ارسال عکس")

    if locks.get("videos") and msg.video:
        return await _del("ارسال ویدیو")

# ─────────────────────────────── ماژول آماده برای اتصال ───────────────────────────────
def register_group_handlers(application):
    """
    🔗 این تابع توسط bot.py صدا زده می‌شود تا هندلرهای مدیریت گروه ثبت شوند.
    """
    from telegram.ext import MessageHandler, filters

    # بررسی پیام‌های گروه برای قفل‌ها
    application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO | filters.VIDEO, check_message_locks))

    print("✅ سیستم گروه با موفقیت به ربات متصل شد.")
