"""
tagger.py
نسخه‌ی کامل، نهایی، سریع و حرفه‌ای — همراه با یوزربات + fallback
تغییرات: اصلاح ساختار، رفع خطای `await outside function`، safe_send ضدفلود،
و fallback امن برای زمانی که یوزربات در دسترس نیست.
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from telegram.error import RetryAfter, TimedOut, TelegramError

# ===================== تنظیمات =====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACTIVITY_FILE = os.path.join(BASE_DIR, "activity.json")

SUDO_IDS = [8588347189]   # شناسه سودو

if not os.path.exists(ACTIVITY_FILE):
    with open(ACTIVITY_FILE, "w", encoding="utf-8") as f:
        json.dump({"activity": {}, "joined": {}}, f, ensure_ascii=False, indent=2)

# ===================== یوزربات (اختیاری) =====================
try:
    from userbot_module.userbot import client as userbot_client
except Exception:
    userbot_client = None

# ===================== فایل داده‌ها =====================
def _load_data():
    try:
        with open(ACTIVITY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"activity": {}, "joined": {}}

def _save_data(data):
    with open(ACTIVITY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ===================== دسترسی =====================
async def _has_access(context, chat_id, user_id):
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except:
        return False


# ===================== رکورد فعالیت =====================
async def record_user_activity(update: Update, context):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if not msg or not user or not chat:
        return

    if chat.type not in ("group", "supergroup"):
        return
    if user.is_bot:
        return

    data = _load_data()
    key = str(chat.id)

    data.setdefault("activity", {})
    data["activity"].setdefault(key, {})
    data["activity"][key][str(user.id)] = datetime.utcnow().timestamp()

    _save_data(data)


# ===================== رکورد ورود کاربران =====================
async def record_new_member(update: Update, context):
    msg = update.effective_message
    new_members = msg.new_chat_members or []
    if not new_members:
        return

    chat = update.effective_chat
    key = str(chat.id)

    data = _load_data()
    data.setdefault("joined", {})
    data["joined"].setdefault(key, {})

    for m in new_members:
        if not m.is_bot:
            data["joined"][key][str(m.id)] = datetime.utcnow().timestamp()

    _save_data(data)


# ===================== گرفتن همه اعضا (یوزربات + fallback امن) =====================
async def get_all_members(chat, context):
    """
    تلاش می‌کند اول با یوزربات همه اعضا را بگیرد.
    اگر یوزربات نباشد یا خطا رخ دهد، برای جلوگیری از
    درخواست‌های سنگین و فلود، fallback امن را اجرا می‌کند:
      - لیست ادمین‌ها برگردانده می‌شود (اگر لازم است می‌توان این بخش را تغییر داد)
    توضیح: ربات‌های تلگرام API عمومی برای گرفتن لیست کامل اعضا ندارند
    (بجز استفاده از userbot / client طرف سوم). بنابراین fallback محدودتر است.
    """
    # ------------------ 1) یوزربات ------------------
    if userbot_client:
        try:
            # برخی یوزربات‌ها متد get_participants دارند؛ در برخی نام متفاوت است.
            members = await userbot_client.get_participants(chat.id)
            if members:
                # تبدیل به آبجکت‌هایی که حداقل .id و .first_name دارند
                result = [m for m in members if not getattr(m, "bot", False)]
                return result
        except Exception:
            # اگر یوزربات خطا داد، به fallback ادامه بده
            pass

    # ------------------ 2) fallback: امن (فقط ادمین‌ها) ------------------
    # چرا؟ به‌خاطر اینکه پیمایش count بزرگ باعث ارسال تعداد زیادی درخواست و فلود می‌شود.
    members = []
    try:
        admins = await context.bot.get_chat_administrators(chat.id)
        for a in admins:
            if a.user and not a.user.is_bot:
                members.append(a.user)
    except Exception:
        # اگر باز هم خطا شد، لیست خالی برگردان
        return []

    return members


# ===================== safe_send ضدفلود =====================
async def safe_send(context, chat_id, text):
    """
    ارسال امن پیام: اگر تلگرام خطای RetryAfter داد، طبق مقادیر گفته شده
    صبر می‌کند و دوباره تلاش می‌کند. اگر Timeout یا خطای غیرمنتظره رخ داد،
    چند ثانیه صبر می‌کند و دوباره سعی می‌کند. در نهایت اگر Markdown باعث
    خطا شد، بدون parse_mode ارسال می‌کند.
    """
    while True:
        try:
            return await context.bot.send_message(chat_id, text, parse_mode="Markdown")
        except RetryAfter as e:
            # تلگرام عدد retry_after به ثانیه می‌دهد
            wait = (getattr(e, "retry_after", None) or 1)
            try:
                # عدد را عددی فرض کن و صبر کن
                await asyncio.sleep(float(wait) + 1)
            except Exception:
                await asyncio.sleep(2)
        except TimedOut:
            await asyncio.sleep(2)
        except TelegramError as e:
            # اگر خطای مرتبط با parse_mode یا متن باشه، تلاش کن بدون Markdown
            try:
                return await context.bot.send_message(chat_id, text)
            except Exception:
                # اگر باز هم خطا داد، کمی صبر کن و retry کن
                await asyncio.sleep(2)
        except Exception:
            # هر خطای دیگر -> کمی صبر و retry
            await asyncio.sleep(1)


# ===================== ساخت پنل =====================
def build_tag_panel():
    kb = [
        [InlineKeyboardButton("𓃬ꪰ همه اعضا", callback_data="tg_all")],
        [InlineKeyboardButton("𓃬ꪰ ادمین‌های فعال", callback_data="tg_admin_active")],
        [InlineKeyboardButton("𓃬ꪰ ادمین‌های غیرفعال", callback_data="tg_admin_inactive")],
        [InlineKeyboardButton("𓃬ꪰ همه کاربران", callback_data="tg_users_all")],
        [InlineKeyboardButton("𓃬ꪰ کاربران فعال", callback_data="tg_users_active")],
        [InlineKeyboardButton("𓃬ꪰ کاربران غیرفعال", callback_data="tg_users_inactive")],
        [InlineKeyboardButton("𓃬ꪰ کاربران جدید", callback_data="tg_new")],
        [InlineKeyboardButton("𓃬ꪰ لیست سفارشی (ریپلای)", callback_data="tg_custom")],
        [InlineKeyboardButton("❌ بستن", callback_data="tg_close")],
    ]
    return InlineKeyboardMarkup(kb)


# ===================== بازکردن پنل =====================
async def open_tag_panel(update: Update, context):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if chat.type not in ("group", "supergroup"):
        return

    if not await _has_access(context, chat.id, user.id):
        return await msg.reply_text("🚫 فقط مدیران اجازه دارند!", quote=True)

    await msg.reply_text("🔽 حالت تگ را انتخاب کنید:", reply_markup=build_tag_panel(), quote=True)


# ===================== ساخت متن تگ =====================
def build_mention_text(items: List[str]) -> List[str]:
    """
    items: لیستی از رشته‌های اشاره‌شده (مثلاً '...[name](tg://user?id=...)')
    خروجی: لیستی از پاراگراف‌ها که هر کدام حداکثر chunk عضو دارند.
    """
    result = []
    chunk = 20  # هر پیام چند اشاره قرار بگیرد — می‌توان این را پایین‌تر برد اگر باز هم فلود شد
    for i in range(0, len(items), chunk):
        result.append("     ".join(items[i:i+chunk]))
    return result


# ===================== هندل تگ =====================
async def handle_tag_panel_click(update: Update, context):
    q = update.callback_query
    await q.answer()

    user = q.from_user
    chat = q.message.chat

    if not await _has_access(context, chat.id, user.id):
        return await q.answer("🚫 دسترسی ندارید!", show_alert=True)

    data = _load_data()
    key = str(chat.id)

    mentions = []

    # ------------------ بستن ------------------
    if q.data == "tg_close":
        try:
            await q.message.delete()
        except:
            pass
        return

    try:
        # ------------------ همه اعضا ------------------
        if q.data == "tg_all":
            members = await get_all_members(chat, context)
            # members ممکن است آبجکت user-like یا آبجکت‌های یوزربات باشند
            mentions = []
            for m in members:
                try:
                    uid = getattr(m, "id", None) or getattr(m, "user_id", None)
                    fname = getattr(m, "first_name", None) or getattr(m, "username", None) or "کاربر"
                    if not uid:
                        continue
                    mentions.append(f"𓃬ꪰ #[{fname}](tg://user?id={uid})")
                except:
                    continue

        # ------------------ ادمین‌ها ------------------
        elif q.data in ("tg_admin_active", "tg_admin_inactive"):
            admins = await context.bot.get_chat_administrators(chat.id)
            cutoff = datetime.utcnow() - timedelta(hours=24)

            for a in admins:
                if a.user.is_bot:
                    continue

                uid = str(a.user.id)
                ts = data.get("activity", {}).get(key, {}).get(uid)
                active = ts and datetime.utcfromtimestamp(ts) > cutoff

                if q.data == "tg_admin_active" and active:
                    mentions.append(f"𓃬ꪰ #[{a.user.first_name}](tg://user?id={a.user.id})")

                if q.data == "tg_admin_inactive" and not active:
                    mentions.append(f"𓃬ꪰ #[{a.user.first_name}](tg://user?id={a.user.id})")

        # ------------------ همه کاربران (غیر ادمین) ------------------
        elif q.data == "tg_users_all":
            members = await get_all_members(chat, context)
            admin_ids = [a.user.id for a in await context.bot.get_chat_administrators(chat.id)]
            mentions = []
            for m in members:
                try:
                    uid = getattr(m, "id", None) or getattr(m, "user_id", None)
                    fname = getattr(m, "first_name", None) or getattr(m, "username", None) or "کاربر"
                    if not uid:
                        continue
                    if uid in admin_ids:
                        continue
                    mentions.append(f"𓃬ꪰ #[{fname}](tg://user?id={uid})")
                except:
                    continue

        # ------------------ کاربران فعال/غیرفعال ------------------
        elif q.data in ("tg_users_active", "tg_users_inactive"):
            cutoff = datetime.utcnow() - timedelta(hours=24)
            act = data.get("activity", {}).get(key, {})

            for uid, ts in act.items():
                try:
                    active = datetime.utcfromtimestamp(ts) > cutoff

                    if q.data == "tg_users_active" and active:
                        mentions.append(f"𓃬ꪰ #[کاربر](tg://user?id={uid})")

                    if q.data == "tg_users_inactive" and not active:
                        mentions.append(f"𓃬ꪰ #[کاربر](tg://user?id={uid})")
                except:
                    continue

        # ------------------ کاربران جدید ------------------
        elif q.data == "tg_new":
            cutoff = datetime.utcnow() - timedelta(days=7)
            joined = data.get("joined", {}).get(key, {})

            for uid, ts in joined.items():
                try:
                    if datetime.utcfromtimestamp(ts) > cutoff:
                        mentions.append(f"𓃬ꪰ #[کاربر جدید](tg://user?id={uid})")
                except:
                    continue

        # ------------------ لیست سفارشی ------------------
        elif q.data == "tg_custom":
            rep = q.message.reply_to_message
            if not rep:
                return await q.answer("باید روی پیام کاربر ریپلای کنید!", show_alert=True)

            u = rep.from_user
            if u and not u.is_bot:
                mentions.append(f"𓃬ꪰ #[{u.first_name}](tg://user?id={u.id})")

    except Exception:
        # در صورت هر خطا، پیامی به کاربر بده و پنل را حذف کن
        try:
            await q.message.edit_text("⚠️ خطا در پردازش!")
            await asyncio.sleep(1)
            await q.message.delete()
        except:
            pass
        return

    # ------------------ بستن پنل ------------------
    try:
        await q.message.delete()
    except:
        pass

    # ------------------ ارسال تگ‌ها ------------------
    # این بخش حتماً داخل تابع (همینجا) قرار دارد تا از خطای await outside function جلوگیری شود
    if mentions:
        parts = build_mention_text(mentions)
        # اگر تعداد پارتی‌ها خیلی زیاد است، بهتر است chunk را کوچکتر بگیریم
        for p in parts:
            await safe_send(context, chat.id, p)
            # این تأخیر نقش ضدفلود را دارد؛ می‌توانید آن را بر حسب تجربه کاهش/افزایش دهید
            await asyncio.sleep(1.2)
    else:
        await safe_send(context, chat.id, "⚠️ هیچ کاربری پیدا نشد.")


# ===================== ثبت هندلرها =====================
def register_tag_handlers(application, group_number: int = 14):

    application.add_handler(
        MessageHandler(filters.Regex("^تگ$") & filters.ChatType.GROUPS, open_tag_panel),
        group=group_number,
    )

    application.add_handler(
        CallbackQueryHandler(handle_tag_panel_click, pattern=r"^tg_"),
        group=group_number + 1,
    )

    application.add_handler(
        MessageHandler(filters.ALL & filters.ChatType.GROUPS, record_user_activity),
        group=group_number + 2,
    )

    application.add_handler(
        MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, record_new_member),
        group=group_number + 3,
    )


# ===================== پایان =====================
