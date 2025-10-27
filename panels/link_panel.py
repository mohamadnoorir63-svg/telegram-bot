# panels/link_panel.py
"""
پنل لینک گروه — ساخت / ابطال / ارسال لینک واقعی
نیازمندی‌ها:
- ربات باید در گروه ادمین باشد و دسترسی Invite Links داشته باشد.
- ذخیره لینک در group_control.json (همان ساختار project شما)
"""

import os
import json
from datetime import datetime, timedelta
from typing import Tuple, Optional, Dict, Any

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ChatInviteLink,
)
from telegram.ext import ContextTypes

# فایل گروه مشترک پروژه (مطمئن شو مسیر با پروژه‌ات مطابقت داره)
BASE_DIR = os.path.dirname(os.path.dirname(__file__)) if os.path.dirname(__file__) else "."
GROUP_CTRL_FILE = os.path.join(BASE_DIR, "group_control.json")

# ================= helper load/save =================
def load_group_data() -> Dict[str, Any]:
    if os.path.exists(GROUP_CTRL_FILE):
        try:
            with open(GROUP_CTRL_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[link_panel] load_group_data error: {e}")
            return {}
    return {}

def save_group_data(data: Dict[str, Any]):
    try:
        with open(GROUP_CTRL_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[link_panel] save_group_data error: {e}")

# ================= utilities برای Invite Link =================
async def bot_is_admin(bot, chat_id: int) -> Tuple[bool, Optional[str]]:
    try:
        me = await bot.get_me()
        member = await bot.get_chat_member(chat_id, me.id)
        if member.status in ("administrator", "creator"):
            return True, None
        return False, "ربات ادمین نیست. برای ساخت لینک ربات باید در گروه ادمین شود."
    except Exception as e:
        return False, f"خطا در بررسی دسترسی ربات: {e}"

async def create_invite_link(bot, chat_id: int,
                             expire_seconds: Optional[int] = None,
                             member_limit: Optional[int] = None,
                             name: Optional[str] = None,
                             creates_join_request: Optional[bool] = None) -> Tuple[Optional[str], Optional[dict]]:
    """
    سعی می‌کنیم از متد create_chat_invite_link استفاده کنیم (اگر wrapper پشتیبانی کند).
    اگر موجود نباشد یا خطا شود از export_chat_invite_link استفاده می‌کنیم (لینک عمومی).
    returns (link, meta_or_error)
    """
    try:
        # برخی wrapperها پارامترها را متفاوت می‌پذیرند؛ ما تلاش می‌کنیم پارامترهای سازگار را ارسال کنیم.
        params = {}
        if expire_seconds:
            params["expire_date"] = int((datetime.utcnow() + timedelta(seconds=expire_seconds)).timestamp())
        if member_limit:
            params["member_limit"] = int(member_limit)
        if name:
            params["name"] = str(name)
        if creates_join_request is not None:
            # این پارامتر در برخی نسخه‌ها معادل درخواست عضویت است.
            params["creates_join_request"] = bool(creates_join_request)

        # تلاش برای create_chat_invite_link
        try:
            link_obj: ChatInviteLink = await bot.create_chat_invite_link(chat_id=chat_id, **params)
            meta = {
                "created_at": datetime.utcnow().isoformat(),
                "expire_date": getattr(link_obj, "expire_date", None).isoformat() if getattr(link_obj, "expire_date", None) else None,
                "member_limit": getattr(link_obj, "member_limit", None),
                "creates_join_request": getattr(link_obj, "creates_join_request", None),
                "name": getattr(link_obj, "name", None)
            }
            return link_obj.invite_link, meta
        except Exception:
            # fallback: export_chat_invite_link (public link)
            link = await bot.export_chat_invite_link(chat_id=chat_id)
            meta = {
                "created_at": datetime.utcnow().isoformat(),
                "expire_date": None,
                "member_limit": None,
                "creates_join_request": None,
                "name": None
            }
            return link, meta

    except Exception as e:
        return None, {"error": str(e)}

async def revoke_invite_link(bot, chat_id: int, invite_link: str) -> Tuple[bool, Optional[str]]:
    """
    تلاش برای revoke_chat_invite_link اگر موجود باشه.
    """
    try:
        # Try to call revoke_chat_invite_link
        try:
            await bot.revoke_chat_invite_link(chat_id=chat_id, invite_link=invite_link)
            return True, None
        except Exception as e:
            # اگر API revoke را پشتیبانی نکند، خطا برمی‌گردانیم و ادامه می‌دهیم تا حداقل لینک جدید بسازیم
            return False, f"عدم پشتیبانی ابطال لینک یا خطا: {e}"
    except Exception as e:
        return False, str(e)

# ================= panel نمایش اولیه =================
async def link_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if not chat or chat.type not in ("group", "supergroup"):
        return await update.message.reply_text("⚠️ این پنل فقط داخل گروه قابل استفاده است.")

    keyboard = [
        [InlineKeyboardButton("📄 نمایش لینک به صورت متن", callback_data="link_show_text")],
        [InlineKeyboardButton("🖼 نمایش کارت لینک", callback_data="link_show_card")],
        [InlineKeyboardButton("🔁 ساخت لینک یک‌بارمصرف", callback_data="link_create_one")],
        [InlineKeyboardButton("🧾 ساخت لینک درخواست عضویت (مثال 24h)", callback_data="link_create_request")],
        [InlineKeyboardButton("✉️ ارسال لینک به پیوی", callback_data="link_send_private")],
        [InlineKeyboardButton("❌ ابطال و ساخت لینک جدید", callback_data="link_revoke_create")],
        [InlineKeyboardButton("📚 راهنما", callback_data="link_guide")],
        [InlineKeyboardButton("◀️ بازگشت", callback_data="link_back")],
    ]
    text = (
        "🔗 <b>پنل مدیریت لینک گروه</b>\n\n"
        "از دکمه‌ها یکی را انتخاب کنید. برای ساخت لینک واقعی، ربات باید در گروه ادمین باشد.\n\n"
        "🔸 لینک یک‌بارمصرف: لینک یک نفر را عضو می‌کند یا منقضی می‌شود.\n"
        "🔸 لینک درخواست عضویت: مثال یک لینک با انقضا 24 ساعت ساخته می‌شود."
    )
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# ================= callback handler =================
async def link_panel_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    chat = query.message.chat
    chat_id = chat.id
    user = query.from_user

    # load group_data
    gdata = load_group_data()
    g = gdata.setdefault(str(chat_id), {})

    def store_link_to_group(link: str, meta: dict):
        invite = {
            "link": link,
            "meta": meta
        }
        g["invite"] = invite
        gdata[str(chat_id)] = g
        save_group_data(gdata)

    # ---------- SHOW TEXT ----------
    if data == "link_show_text":
        inv = g.get("invite")
        if inv and inv.get("link"):
            meta = inv.get("meta", {})
            text = (
                f"🔗 <b>لینک گروه:</b>\n\n{inv['link']}\n\n"
                f"• ساخته شده: {meta.get('created_at')}\n"
                f"• انقضا: {meta.get('expire_date') or 'هیچ'}\n"
                f"• محدودیت عضو: {meta.get('member_limit') or 'بدون محدودیت'}\n"
                f"• درخواست عضویت: {meta.get('creates_join_request')}\n"
            )
            return await query.message.reply_text(text, parse_mode="HTML")
        # اگر ذخیره نشده تلاش برای گرفتن لینک فعلی
        ok, err = await bot_is_admin(context.bot, chat_id)
        try:
            if not ok:
                # اگر ربات ادمین نیست، ولی ممکنه گروه لینک عمومی داشته باشه => exportChatInviteLink خطا میده مگر ربات ادمین باشه
                return await query.message.reply_text("ℹ️ هیچ لینکی در حافظه ثبت نشده. برای ساخت یا مشاهده لینک، ربات باید ادمین شود.")
            # امتحان export (fallback)
            link = await context.bot.export_chat_invite_link(chat_id)
            meta = {"created_at": datetime.utcnow().isoformat(), "expire_date": None, "member_limit": None, "creates_join_request": None}
            store_link_to_group(link, meta)
            return await query.message.reply_text(f"🔗 لینک گروه دریافت شد:\n{link}")
        except Exception as e:
            return await query.message.reply_text(f"⚠️ خطا در دریافت لینک گروه: {e}")

    # ---------- SHOW CARD ----------
    if data == "link_show_card":
        inv = g.get("invite")
        if inv and inv.get("link"):
            caption = (
                f"📌 <b>{chat.title}</b>\n\n"
                f"🔗 {inv['link']}\n\n"
                f"• محدودیت: {inv['meta'].get('member_limit') or 'بدون'}\n"
                f"• انقضا: {inv['meta'].get('expire_date') or 'هیچ'}"
            )
            return await query.message.reply_text(caption, parse_mode="HTML")
        return await query.message.reply_text("ℹ️ لینک ذخیره نشده است یا باید اول لینک بسازید.")

    # ---------- CREATE ONE-TIME ----------
    if data == "link_create_one":
        ok, err = await bot_is_admin(context.bot, chat_id)
        if not ok:
            return await query.message.reply_text(err or "ربات باید ادمین باشد.")
        # ساخت لینک یکبارمصرف: member_limit=1 ، expire 24h
        link, meta = await create_invite_link(context.bot, chat_id, expire_seconds=24*3600, member_limit=1, name="one-time-link")
        if not link:
            return await query.message.reply_text(f"⚠️ خطا در ساخت لینک: {meta}")
        store_link_to_group(link, meta)
        return await query.message.reply_text(f"✅ لینک یکبارمصرف ساخته شد:\n{link}")

    # ---------- CREATE REQUEST (مثال 24h) ----------
    if data == "link_create_request":
        ok, err = await bot_is_admin(context.bot, chat_id)
        if not ok:
            return await query.message.reply_text(err or "ربات باید ادمین باشد.")
        # این نسخه یک لینک با انقضا 24 ساعت و بدون محدودیت می‌سازد (مثال)
        link, meta = await create_invite_link(context.bot, chat_id, expire_seconds=24*3600, member_limit=None, name="request-link", creates_join_request=True)
        if not link:
            return await query.message.reply_text(f"⚠️ خطا در ساخت لینک: {meta}")
        store_link_to_group(link, meta)
        return await query.message.reply_text(f"✅ لینک درخواست عضویت ساخته شد:\n{link}")

    # ---------- SEND TO PRIVATE ----------
    if data == "link_send_private":
        inv = g.get("invite")
        if not inv or not inv.get("link"):
            return await query.message.reply_text("ℹ️ هنوز لینکی ساخته نشده. از گزینه ساخت لینک استفاده کن.")
        link = inv["link"]
        try:
            await context.bot.send_message(user.id, f"🔗 لینک گروه <b>{chat.title}</b>:\n\n{link}", parse_mode="HTML")
            return await query.message.reply_text("✅ لینک به پیوی شما ارسال شد. (اگر اول به ربات پیام نداده باشید ارسال نمیشود.)")
        except Exception as e:
            return await query.message.reply_text("⚠️ ارسال به پیوی ناموفق است. ابتدا به ربات پیام بده تا بتوانم لینک را ارسال کنم.")

    # ---------- REVOKE & CREATE ----------
    if data == "link_revoke_create":
        inv = g.get("invite")
        if inv and inv.get("link"):
            link = inv["link"]
            ok_revoked, err_rev = await revoke_invite_link(context.bot, chat_id, link)
            # حتی اگر ابطال موفق نبود، ما همچنان لینک جدید می‌سازیم و ذخیره می‌کنیم
        else:
            ok_revoked, err_rev = (False, None)
        # ساخت لینک جدید (بدون محدودیت)
        ok, err_admin = await bot_is_admin(context.bot, chat_id)
        if not ok:
            return await query.message.reply_text(err_admin or "ربات باید ادمین باشد.")
        new_link, meta = await create_invite_link(context.bot, chat_id)
        if not new_link:
            return await query.message.reply_text(f"⚠️ خطا در ساخت لینک جدید: {meta}")
        store_link_to_group(new_link, meta)
        txt = "✅ لینک جدید ساخته شد:\n" + new_link
        if not ok_revoked and err_rev:
            txt += f"\n\n⚠️ توجه: لینک قبلی نتوانست ابطال شود:\n{err_rev}"
        return await query.message.reply_text(txt)

    # ---------- GUIDE ----------
    if data == "link_guide":
        guide = (
            "📚 راهنمای مدیریت لینک گروه\n\n"
            "• ربات باید ادمین باشد و دسترسی Invite Links را داشته باشد.\n"
            "• لینک یک‌بارمصرف: معمولاً member_limit=1 (یک عضویت) یا با ایجاد درخواست عضویت ترکیب می‌شود.\n"
            "• ابطال لینک: اگر API اجازه دهد revoke انجام می‌شود؛ اگر نه لینک جدید ساخته می‌شود و لینک قبلی از حافظه پاک می‌شود.\n"
            "• برای ارسال لینک به پیوی کاربر، او باید قبلاً حداقل یک پیام به ربات ارسال کرده باشد.\n\n"
            "⬅️ بازگشت به پنل: دکمه بازگشت را بزنید."
        )
        return await query.message.reply_text(guide)

    # ---------- BACK ----------
    if data == "link_back":
        # سعی کن اگر پروژه‌ات تابعی برای نمایش منوی اصلی داره، اون رو فراخوانی کنی.
        # به صورت محافظه‌کار، اگر show_main_panel موجود نبود، پیام ساده ارسال می‌کنیم.
        try:
            # از bot.py یا جای دیگر تابع show_main_panel رو فراخوانی کن اگر دارید
            from bot import show_main_panel
            # show_main_panel ممکنه signature متفاوت داشته باشه؛ تلاش می‌کنیم متداول‌ترین رو اجرا کنیم
            try:
                await show_main_panel(update, context, edit=False)
            except TypeError:
                # fallback اگر signature فرق دارد
                await show_main_panel(update, context)
        except Exception:
            # اگر تابع وجود نداشت فقط یک متن مینویسیم
            return await query.message.reply_text("🔙 بازگشت انجام شد. برای نمایش منوی اصلی /start را بزنید.")

    # fallback
    await query.message.reply_text("⚠️ گزینه نامشخص.")
