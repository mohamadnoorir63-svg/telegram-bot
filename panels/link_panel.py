# panels/link_panel.py
import os
import json
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatInviteLink
from telegram.ext import ContextTypes

# مسیر فایل گروه (همان فایلی که در group_control.json استفاده می‌کنید)
GROUP_CTRL_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "group_control.json")
BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

# helper load/save (سازگار با ساختار پروژه شما)
def load_group_data():
    if os.path.exists(GROUP_CTRL_FILE):
        try:
            with open(GROUP_CTRL_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_group_data(data):
    try:
        with open(GROUP_CTRL_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[link_panel] save error: {e}")

# ساختار دادهٔ ذخیره‌شده برای invite (داخل group_data[chat_id]['invite'])
# { "link": "...", "expire_at": "... or None", "member_limit": 0, "one_time": False, "created_at": "ISO" }

# ======================= پنل اصلی لینک =======================
async def link_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش پنل لینک گروه — فقط در گروه"""
    chat = update.effective_chat
    user = update.effective_user

    if chat.type not in ["group", "supergroup"]:
        return await update.message.reply_text("⚠️ این پنل فقط داخل گروه کار می‌کند.")

    keyboard = [
        [InlineKeyboardButton("📄 نمایش لینک بصورت متن", callback_data="link_show_text")],
        [InlineKeyboardButton("🖼 نمایش لینک به‌صورت عکس/کارت", callback_data="link_show_card")],
        [InlineKeyboardButton("🔁 ساخت لینک یکبار مصرف", callback_data="link_create_one")],
        [InlineKeyboardButton("🧾 ساخت لینک درخواست عضویت (قابل تنظیم)", callback_data="link_create_request")],
        [InlineKeyboardButton("✉️ ارسال لینک به پیوی", callback_data="link_send_private")],
        [InlineKeyboardButton("❌ ابطال و ساخت لینک جدید", callback_data="link_revoke_create")],
        [InlineKeyboardButton("📚 راهنمای فعال‌سازی", callback_data="link_guide")],
        [InlineKeyboardButton("◀️ بازگشت", callback_data="link_back")]
    ]
    msg = (
        "🔗 <b>پنل مدیریت لینک گروه</b>\n\n"
        "از دکمه‌های زیر استفاده کنید:\n\n"
        "• نمایش یا ساخت لینک واقعی گروه\n"
        "• ساخت لینک یک‌بارمصرف یا محدود به تعداد\n"
        "• ابطال لینک قبلی و ساخت لینک جدید\n"
    )
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

# ======================= توابع کمکی تعامل با API تلگرام =======================
async def _create_chat_invite(bot, chat_id:int, expire_seconds:int=0, member_limit:int=0, one_time:bool=False):
    """
    تلاش برای ساخت invite link با متد create_chat_invite_link (در صورت پشتیبانی)
    در غیر اینصورت fallback به export_chat_invite_link
    return: (link_str, meta_dict) or (None, err_msg)
    """
    try:
        # سعی می‌کنیم از create_chat_invite_link جدید استفاده کنیم
        # کار با نسخه‌های مختلف API ممکنه متفاوت باشه، پس try/except
        params = {}
        if expire_seconds and expire_seconds > 0:
            params["expire_date"] = datetime.utcnow() + timedelta(seconds=expire_seconds)
        if member_limit and member_limit > 0:
            params["member_limit"] = member_limit
        if one_time:
            params["creates_join_request"] = False  # 'one_time' به member_limit/expire وابسته است؛ بعضی API ها پارامتر خاص دارند
            # بعضی نسخه ها پارامتر 'is_revoked' یا 'creates_join_request' دارن؛ اینجا ساده نگه میداریم

        # اگر create_chat_invite_link در wrapper موجود باشه:
        try:
            link_obj: ChatInviteLink = await bot.create_chat_invite_link(chat_id=chat_id, **({} if not params else params))
            return (link_obj.invite_link, {
                "expires_at": link_obj.expire_date.isoformat() if getattr(link_obj, "expire_date", None) else None,
                "member_limit": getattr(link_obj, "member_limit", None),
                "one_time": getattr(link_obj, "creates_join_request", False)
            })
        except Exception:
            # fallback: exportChatInviteLink (قدیمی)
            link = await bot.export_chat_invite_link(chat_id)
            return (link, {"expires_at": None, "member_limit": 0, "one_time": False})
    except Exception as e:
        return (None, f"خطا در ساخت لینک: {e}")

async def _revoke_chat_invite(bot, chat_id:int, invite_link:str):
    """
    تلاش برای ابطال لینک (revoke). اگر متد revoke موجود نیست، فقط حذف از ذخیره محلی انجام می‌شود.
    """
    try:
        # Try revoke_chat_invite_link if available
        try:
            await bot.revoke_chat_invite_link(chat_id=chat_id, invite_link=invite_link)
            return True, None
        except Exception:
            # If no revoke method, try create_chat_invite_link with creates_join_request True? (not reliable)
            return False, "ربات نتوانست لینک را ابطال کند (API پشتیبانی نمی‌کند)."
    except Exception as e:
        return False, str(e)

# ======================= پردازش دکمه‌ها =======================
async def link_panel_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data  # e.g. "link_show_text"
    chat = query.message.chat
    chat_id = chat.id
    user = query.from_user

    # بارگذاری داده‌ها
    gdata = load_group_data()
    chat_key = str(chat_id)
    group = gdata.setdefault(chat_key, {})

    # helper برای ذخیره invite در group_data
    def _store_invite(link_str, meta):
        invite = {
            "link": link_str,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": meta.get("expires_at"),
            "member_limit": meta.get("member_limit", 0),
            "one_time": meta.get("one_time", False)
        }
        group["invite"] = invite
        gdata[chat_key] = group
        save_group_data(gdata)

    # نمایش لینک در متن
    if data == "link_show_text":
        inv = group.get("invite")
        if inv and inv.get("link"):
            text = (
                f"🔗 <b>لینک گروه:</b>\n\n"
                f"{inv['link']}\n\n"
                f"• ساخت در: {inv.get('created_at')}\n"
                f"• انقضا: {inv.get('expires_at') or 'هیچ'}\n"
                f"• محدودیت عضو: {inv.get('member_limit',0)}\n"
                f"• یک‌بارمصرف: {'بله' if inv.get('one_time') else 'خیر'}"
            )
            await query.message.reply_text(text, parse_mode="HTML")
        else:
            # اگر لینک ذخیره نشده، تلاش برای گرفتن لینک فعلی از تلگرام
            try:
                # exportChatInviteLink ممکنه کار کنه
                link = await context.bot.export_chat_invite_link(chat_id)
                meta = {"expires_at": None, "member_limit": 0, "one_time": False}
                _store_invite(link, meta)
                await query.message.reply_text(f"🔗 لینک جدید دریافت شد:\n{link}")
            except Exception as e:
                await query.message.reply_text(f"⚠️ خطا در گرفتن لینک گروه (ربات باید ادمین و دسترسی تولید لینک داشته باشد):\n{e}")

        return

    # نمایش کارت/عکس — در اینجا کارت ساده با متن، می‌توان بعداً عکس اختصاصی فرستاد
    if data == "link_show_card":
        inv = group.get("invite")
        if inv and inv.get("link"):
            caption = (
                f"📌 <b>لینک گروه</b>\n\n"
                f"• نام گروه: <b>{chat.title}</b>\n"
                f"• لینک: {inv['link']}\n"
                f"• محدودیت: {inv.get('member_limit', 0)}\n"
            )
            await query.message.reply_text(caption, parse_mode="HTML")
        else:
            await query.message.reply_text("ℹ️ هنوز لینکی ساخته یا ذخیره نشده است. از گزینه ساخت لینک استفاده کنید.")
        return

    # ساخت لینک یک‌بارمصرف (یکبار مصرف = member_limit=1 یا creates_join_request ?)
    if data == "link_create_one":
        # بررسی ادمین بودن ربات و دسترسی
        try:
            me = await context.bot.get_me()
            bot_member = await context.bot.get_chat_member(chat_id, me.id)
            if bot_member.status not in ["administrator", "creator"]:
                return await query.message.reply_text("⚠️ ربات باید ادمین باشد تا بتواند لینک بسازد.")
        except Exception as e:
            return await query.message.reply_text(f"⚠️ خطا: {e}")

        # ایجاد لینک یک‌بارمصرف (member_limit=1 ،expire 24h فرضی)
        link, meta_or_err = await _create_chat_invite(context.bot, chat_id, expire_seconds=24*3600, member_limit=1, one_time=True)
        if not link:
            return await query.message.reply_text(f"⚠️ خطا در ساخت لینک: {meta_or_err}")

        _store_invite(link, meta_or_err)
        await query.message.reply_text(f"✅ لینک یک‌بارمصرف ساخته شد:\n{link}")
        return

    # ساخت لینک درخواست عضویت (قابل تنظیم) — ما یک لینک 24 ساعت با محدودیت 1 یا بیشتر می‌سازیم (مثال)
    if data == "link_create_request":
        try:
            me = await context.bot.get_me()
            bot_member = await context.bot.get_chat_member(chat_id, me.id)
            if bot_member.status not in ["administrator", "creator"]:
                return await query.message.reply_text("⚠️ ربات باید ادمین باشد تا بتواند لینک بسازد.")
        except Exception as e:
            return await query.message.reply_text(f"⚠️ خطا: {e}")

        # اینجا ساده: از کاربر می‌پرسیم آیا می‌خواهد لینک باقابلیت (24 ساعت/۱ نفر) یا بدون محدودیت باشد
        # برای سادگی یک لینک 24 ساعت/عضویت یک نفر می‌سازیم (می‌توانید فرم ورودی اضافه کنید)
        link, meta_or_err = await _create_chat_invite(context.bot, chat_id, expire_seconds=24*3600, member_limit=1)
        if not link:
            return await query.message.reply_text(f"⚠️ خطا در ساخت لینک: {meta_or_err}")

        _store_invite(link, meta_or_err)
        await query.message.reply_text(f"✅ لینک درخواست عضویت ساخته شد:\n{link}")
        return

    # ارسال لینک به پیوی کاربر
    if data == "link_send_private":
        inv = group.get("invite")
        if not inv or not inv.get("link"):
            # تلاش برای گرفتن لینک فعلی
            try:
                link = await context.bot.export_chat_invite_link(chat_id)
                meta = {"expires_at": None, "member_limit": 0, "one_time": False}
                _store_invite(link, meta)
                inv = group.get("invite")
            except Exception as e:
                return await query.message.reply_text(f"⚠️ لینک موجود نیست و ربات نتوانست لینک گروه را دریافت کند:\n{e}")

        try:
            await context.bot.send_message(chat_id=user.id, text=f"🔗 لینک گروه <b>{chat.title}</b>:\n\n{inv['link']}", parse_mode="HTML")
            await query.message.reply_text("✅ لینک به پیوی شما ارسال شد. (اگر قبلاً به ربات پیام نداده‌اید، ابتدا یک پیام به ربات بفرستید.)")
        except Exception as e:
            await query.message.reply_text("⚠️ ارسال به پیوی ناموفق بود. لطفاً ابتدا به ربات پیامی بفرستید تا بتوانم لینک را ارسال کنم.")
        return

    # ابطال و ساخت لینک جدید
    if data == "link_revoke_create":
        inv = group.get("invite")
        if inv and inv.get("link"):
            ok, err = await _revoke_chat_invite(context.bot, chat_id, inv["link"])
            if not ok:
                # حتی اگر ابطال نشد، ما سعی می‌کنیم لینک جدید بسازیم و جایگزین کنیم (تا لینک ذخیره شده بروز شود)
                pass

        # ساخت یک لینک جدید (بدون محدودیت)
        try:
            link, meta_or_err = await _create_chat_invite(context.bot, chat_id)
            if not link:
                return await query.message.reply_text(f"⚠️ خطا در ساخت لینک جدید: {meta_or_err}")
            _store_invite(link, meta_or_err)
            await query.message.reply_text(f"✅ لینک جدید ساخته و جایگزین شد:\n{link}")
        except Exception as e:
            await query.message.reply_text(f"⚠️ خطا در ابطال/ساخت لینک جدید: {e}")
        return

    # راهنما (modal-like) — ما ساده متن راهنما می‌فرستیم
    if data == "link_guide":
        guide_text = (
            "📚 راهنمای مدیریت لینک گروه\n\n"
            "• برای ساخت یا ابطال لینک، ربات باید ادمین باشد و دسترسی ساخت لینک را داشته باشد.\n"
            "• لینک یک‌بارمصرف: لینک فقط یک نفر را می‌تواند عضو کند یا منقضی شود.\n"
            "• برای ارسال لینک به پیوی کاربران، آن‌ها باید قبلاً حداقل یک پیام به ربات فرستاده باشند.\n"
            "• اگر ربات نتوانست لینک را ابطال کند، ممکن است API محدودیت داشته باشد؛ در این صورت لینک جدید ساخته می‌شود."
        )
        await query.message.reply_text(guide_text)
        return

    # بازگشت (back)
    if data == "link_back":
        # اگر پنل اصلی شما تابع show_main_panel دارد، بهتر است آن را صدا بزنی.
        # اینجا فقط یک پیام ساده ارسال می‌کنیم تا کاربر به منو بازگردد.
        # اگر در پروژه‌ی شما تابع show_main_panel در دسترس است، آن را import و فراخوانی کن.
        try:
            from bot import show_main_panel  # در صورتی که تابع در bot.py موجود است
            # ساخت یک fake update / callback مشابه قبل
            await show_main_panel(update, context, edit=False)
        except Exception:
            await query.message.reply_text("🔙 بازگشت انجام شد. برای باز کردن منوی اصلی /start را بزنید.")
        return

    # fallback
    await query.message.reply_text("⚠️ گزینه نامشخص یا پشتیبانی‌نشده.")
