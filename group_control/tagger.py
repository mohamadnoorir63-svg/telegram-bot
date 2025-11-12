# tag_bot.py
import os
import json
import time
import asyncio
import random
from datetime import datetime
from typing import List, Dict, Optional

from telegram import Update, User
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)

# ===================== تنظیمات =====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACTIVITY_FILE = os.path.join(BASE_DIR, "activity.json")
CONFIG_FILE = os.path.join(BASE_DIR, "tag_config.json")

# آیدی های سودو/صاحبان ربات (اینجا نمونه است، مقدار صحیح را بگذار)
SUDO_IDS = [8588347189]

# مقدار پیش‌فرض برای تعداد کاربران در هر پیام (تلگرام پیام خیلی طولانی قبول نمی‌کند)
MENTION_CHUNK = 20

# مقدار پیش‌فرض برای اسکن (تعداد آیدی‌هایی که در حالت full_scan هر بار بررسی می‌کنیم)
DEFAULT_FULL_SCAN_STEP = 200

# فایل‌ها را بساز اگر هست ندارند
for f in (ACTIVITY_FILE, CONFIG_FILE):
    if not os.path.exists(f):
        with open(f, "w", encoding="utf-8") as fh:
            json.dump({}, fh, ensure_ascii=False, indent=2)


# --------------------- ذخیره/بارگذاری ---------------------
def load_json(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_json(path: str, obj: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


# ====================== کمکی‌ها ======================
def is_sudo(uid: int) -> bool:
    return uid in SUDO_IDS


async def has_access(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> bool:
    """بررسی اینکه کاربر سودو هست یا مدیر گروه است."""
    if is_sudo(user_id):
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except Exception:
        return False


def chunkify(lst: List[str], size: int) -> List[List[str]]:
    return [lst[i:i + size] for i in range(0, len(lst), size)]


# ====================== ثبت فعالیت ======================
async def record_user_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هر پیامی که کاربر ارسال کند، آیدی و نام را ذخیره می‌کنیم."""
    msg = update.effective_message
    if not msg:
        return
    chat = update.effective_chat
    user = update.effective_user
    if not chat or chat.type not in ("group", "supergroup"):
        return
    if not user or user.is_bot:
        return

    data = load_json(ACTIVITY_FILE)
    chat_key = str(chat.id)
    if chat_key not in data:
        data[chat_key] = {}
    data[chat_key][str(user.id)] = {
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
        "username": user.username or "",
        "last_seen": datetime.utcnow().isoformat(),
    }
    save_json(ACTIVITY_FILE, data)


# همچنین عضو شدن جدید را ذخیره کن
async def handle_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg or not msg.new_chat_members:
        return
    chat = update.effective_chat
    data = load_json(ACTIVITY_FILE)
    chat_key = str(chat.id)
    if chat_key not in data:
        data[chat_key] = {}
    for u in msg.new_chat_members:
        if u.is_bot:
            continue
        data[chat_key][str(u.id)] = {
            "first_name": u.first_name or "",
            "last_name": u.last_name or "",
            "username": u.username or "",
            "last_seen": datetime.utcnow().isoformat(),
        }
    save_json(ACTIVITY_FILE, data)


# ====================== جمع‌آوری اعضا برای تگ ======================
async def gather_members_for_tag(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    require_full_scan: bool = False,
    max_scan_total: int = 1000
) -> List[Dict]:
    """
    این تابع مجموعه‌ای از کاربران قابل تگ را برمی‌گرداند.
    - اول از cache/activity استفاده می‌کند (کاربران پیام‌دهنده یا وارد شده).
    - سپس admins را اضافه می‌کند.
    - در صورت نیاز و با حالت full_scan=True تلاش خزنده‌ای برای یافتن اعضای بیشتر انجام می‌دهد
      (با get_chat_member روی ranges عددی). این بخش ریسک rate-limit دارد — با احتیاط.
    """
    collected = {}
    # 1) از activity.json بخوان
    activity = load_json(ACTIVITY_FILE).get(str(chat_id), {})
    for uid_str, info in activity.items():
        try:
            uid = int(uid_str)
        except:
            continue
        collected[uid] = info

    # 2) اضافه کردن admin ها
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        for a in admins:
            u = a.user
            if u.is_bot:
                continue
            collected[u.id] = {
                "first_name": u.first_name or "",
                "last_name": u.last_name or "",
                "username": u.username or "",
                "last_seen": datetime.utcnow().isoformat(),
            }
    except Exception:
        pass

    # 3) اگر نیاز به اسکن کامل داریم (اختیاری و خطرناک از نظر نرخ) — محافظت شده
    if require_full_scan:
        # member_count را بگیریم (تعداد تقریبی اعضا)
        try:
            chat_obj = await context.bot.get_chat(chat_id)
            member_count = getattr(chat_obj, "members_count", None) or getattr(chat_obj, "member_count", None)
            if not member_count:
                member_count = 0
        except Exception:
            member_count = 0

        # strategy: اگر تعداد قابل قبول است، بدنه‌ای از آیدی‌های معقول را تلاش می‌کنیم
        # نکته: آیدی‌های تلگرام پراکنده‌اند؛ این روش تضمینی نیست.
        # ما به جای scan از 1..N، محدوده‌هایی اطراف آیدی‌های شناخته‌شده را امتحان می‌کنیم.
        known_ids = sorted(collected.keys())
        probes = []
        if known_ids:
            # برای هر شناخته‌شده +- range را امتحان کن
            for k in known_ids:
                start = max(1, k - 500)
                end = k + 500
                probes.extend(range(start, end + 1))
        else:
            # اگر هیچ کاربری نداریم، سعی می‌کنیم از member_count تخمین بزنیم:
            # (این فقط یک تلاش است؛ اغلب ناکارآمد)
            probes = list(range(max(1, member_count - max_scan_total), member_count + 1))

        # محدودش کن تا از max_scan_total فراتر نرود
        probes = list(dict.fromkeys(probes))  # یکتا کن با حفظ ترتیب
        if len(probes) > max_scan_total:
            probes = probes[:max_scan_total]

        # حالا با احتیاط get_chat_member بزن (تا rate-limit کمتر شود)
        for uid in probes:
            if uid in collected:
                continue
            try:
                cm = await context.bot.get_chat_member(chat_id, uid)
                u = cm.user
                if u.is_bot:
                    continue
                collected[u.id] = {
                    "first_name": u.first_name or "",
                    "last_name": u.last_name or "",
                    "username": u.username or "",
                    "last_seen": datetime.utcnow().isoformat(),
                }
                # کمی مکث برای جلوگیری از سرعت بیش از حد
                await asyncio.sleep(0.05)
            except Exception:
                # ignore failures (کاربر نیست یا محدودیت)
                await asyncio.sleep(0.02)
                continue

    # برگردان لیست کاربران به صورت دیکشن
    members = []
    for uid, info in collected.items():
        members.append({
            "id": uid,
            "first_name": info.get("first_name", "") or "",
            "username": info.get("username", "") or "",
        })
    # مرتب کن (اختیاری) — بر اساس نام
    members.sort(key=lambda x: (x["first_name"] or "").lower())
    return members


# ====================== فرمان: تگ همه ======================
async def cmd_tag_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    دستور:
      تگ همه         -> تگ از cached members و admins
      تگ همه full    -> تلاش اسکن (کند) برای یافتن اعضای بیشتر (ریسک rate-limit)
    """
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if not msg or not chat or chat.type not in ("group", "supergroup"):
        return

    # دسترسی: فقط مدیر یا سودو
    if not await has_access(context, chat.id, user.id):
        return await msg.reply_text("🚫 فقط مدیران یا سودوها مجاز به اجرای این دستور هستند.")

    args = context.args or []
    full = False
    if args and "full" in args:
        full = True

    # بازخورد اولیه
    sent = await msg.reply_text("⏳ در حال جمع‌آوری لیست اعضا... (full_scan={})".format(full))

    try:
        members = await gather_members_for_tag(context, chat.id, require_full_scan=full, max_scan_total=1000)
    except Exception as e:
        await sent.edit_text(f"❌ خطا در جمع‌آوری اعضا: {e}")
        return

    if not members:
        await sent.edit_text("⚠️ هیچ عضوی برای تگ یافت نشد.")
        return

    # آماده‌سازی پیام‌ها با chunk
    mention_texts = []
    for m in members:
        uid = m["id"]
        name = (m["first_name"] or "کاربر")
        mention_texts.append(f"[{name}](tg://user?id={uid})")

    chunks = chunkify(mention_texts, MENTION_CHUNK)
    sent.edit_text(f"🔔 شروع ارسال تگ‌ها — تعداد کل: {len(mention_texts)} (با {len(chunks)} پیام)")

    sent_count = 0
    for chunk in chunks:
        try:
            await context.bot.send_message(chat.id, "👥 " + " ".join(chunk), parse_mode="Markdown")
            sent_count += len(chunk)
            await asyncio.sleep(1.0)  # مکث بین پیام‌ها — می‌توان کمتر/بیشتر کرد
        except Exception as e:
            # در صورت خطا، لاگ کن و ادامه بده
            print("tag_all chunk error:", e)
            await asyncio.sleep(1.0)
            continue

    await context.bot.send_message(chat.id, f"✅ تگ همه تمام شد. ({sent_count} تگ ارسال شد)")

# ====================== فرمان: تست ======================
async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("pong")


# ====================== ثبت هندلرها و اجرا ======================
def main():
    TOKEN = os.environ.get("BOT_TOKEN")
    if not TOKEN:
        print("ERROR: set BOT_TOKEN in env")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    # هندلرهای ثبت فعالیت (پیام‌ها و ورود اعضا)
    app.add_handler(MessageHandler(filters.ALL & filters.ChatType.GROUPS, record_user_activity), group=1)
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS & filters.ChatType.GROUPS, handle_new_members), group=1)

    # فرمان تگ همه: کاربر باید پیام بزند "تگ همه" (یا با آرگومان "full")
    app.add_handler(CommandHandler("tagall", cmd_tag_all))  # /tagall full (برای آزمایش)
    # همچنین یک هندلر متنی برای دستور فارسی مستقیم:
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^تگ\s*همه\b"), lambda u, c: cmd_tag_all(u, c)), group=5)

    app.add_handler(CommandHandler("ping", cmd_ping))

    print("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
