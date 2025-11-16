# panels/link_panel.py
import os, json
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatInviteLink
from telegram.ext import ContextTypes

# 📂 مسیر فایل داده گروه‌ها
GROUP_CTRL_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "group_control.json")
SUDO_IDS = [8588347189]  # آیدی سودو اصلی

# ===================== 🗂 مدیریت فایل =====================
def load_group_data():
    if os.path.exists(GROUP_CTRL_FILE):
        try:
            with open(GROUP_CTRL_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_group_data(data):
    with open(GROUP_CTRL_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ⚡ جایگزینی سریع پیام (بدون تاخیر)
async def fast_replace(query, text, keyboard=None, parse_mode="HTML"):
    try:
        await query.message.delete()
    except:
        pass
    await query.message.chat.send_message(
        text=text,
        parse_mode=parse_mode,
        reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None
    )

# ===================== 🧭 پنل اصلی =====================
async def link_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type not in ["group", "supergroup"]:
        return await update.message.reply_text("⚠️ فقط در گروه قابل استفاده است.")

    # بررسی دسترسی مدیر یا سودو
    async def _has_access(user_id):
        if user_id in SUDO_IDS:
            return True
        try:
            member = await context.bot.get_chat_member(chat.id, user_id)
            return member.status in ("creator", "administrator")
        except:
            return False

    if not await _has_access(user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودو می‌توانند از پنل استفاده کنند.")

    gdata = load_group_data()
    group = gdata.setdefault(str(chat.id), {})

    keyboard = generate_main_keyboard()
    text = get_panel_text()
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

# ===================== ⚙️ کنترل دکمه‌ها =====================
async def link_panel_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    chat = query.message.chat
    chat_id = chat.id
    user = query.from_user

    # بررسی دسترسی مدیر یا سودو
    async def _has_access(user_id):
        if user_id in SUDO_IDS:
            return True
        try:
            member = await context.bot.get_chat_member(chat_id, user_id)
            return member.status in ("creator", "administrator")
        except:
            return False

    if not await _has_access(user.id):
        return await query.answer(
            "🚫 فقط مدیران یا سودو می‌توانند این بخش را استفاده کنند.",
            show_alert=True
        )

    await query.answer()  # پاسخ اولیه برای جلوگیری از ساعت‌گرد شدن دکمه

    gdata = load_group_data()
    group = gdata.setdefault(str(chat_id), {})

    def store_link(link, meta):
        group["invite"] = {"link": link, "created": datetime.now().isoformat(), "meta": meta}
        gdata[str(chat_id)] = group
        save_group_data(gdata)

    # ========= نمایش لینک =========
    if data == "link_show":
        inv = group.get("invite")
        if inv and inv.get("link"):
            text = f"🔗 <b>لینک فعلی گروه:</b>\n\n{inv['link']}"
        else:
            try:
                link = await context.bot.export_chat_invite_link(chat_id)
                store_link(link, {"type": "default"})
                text = f"✅ لینک جدید ساخته شد:\n{link}"
            except Exception as e:
                text = f"⚠️ ربات باید ادمین باشد تا لینک را بگیرد.\n\n<code>{e}</code>"

        kb = [[InlineKeyboardButton("🔙 بازگشت", callback_data="link_main")]]
        return await fast_replace(query, text, kb)

    # ========= ارسال لینک به پیوی =========
    if data == "link_send_pm":
        inv = group.get("invite")
        if not inv or not inv.get("link"):
            try:
                link = await context.bot.export_chat_invite_link(chat_id)
                store_link(link, {"type": "default"})
            except Exception as e:
                return await query.answer(f"⚠️ خطا در ساخت لینک:\n{e}", show_alert=True)
        try:
            await context.bot.send_message(user.id, f"🔗 لینک گروه:\n{group['invite']['link']}")
            await query.answer("✅ لینک برای شما در پیام خصوصی ارسال شد.")
        except Exception:
            await query.answer("⚠️ لطفاً ابتدا به ربات پیام بدهید تا لینک ارسال شود.", show_alert=True)

    # ========= ساخت لینک دائمی =========
    if data == "link_create_confirm":
        kb = [
            [InlineKeyboardButton("✅ بله، بساز", callback_data="link_create_yes")],
            [InlineKeyboardButton("❌ انصراف", callback_data="link_main")]
        ]
        text = "آیا مطمئنی می‌خوای یک لینک جدید بسازی؟\n\nلینک قبلی همچنان فعال می‌مونه."
        return await fast_replace(query, text, kb)

    if data == "link_create_yes":
        try:
            link_obj: ChatInviteLink = await context.bot.create_chat_invite_link(chat_id)
            store_link(link_obj.invite_link, {"type": "permanent"})
            text = f"✅ لینک جدید ساخته شد:\n{link_obj.invite_link}"
        except Exception:
            link = await context.bot.export_chat_invite_link(chat_id)
            store_link(link, {"type": "fallback"})
            text = f"✅ لینک جدید ساخته شد:\n{link}"

        kb = [[InlineKeyboardButton("🔙 بازگشت", callback_data="link_main")]]
        return await fast_replace(query, text, kb)

    # ========= ساخت لینک محدود =========
    if data == "link_temp_ask":
        kb = [
            [
                InlineKeyboardButton("👥 1", callback_data="link_temp_1"),
                InlineKeyboardButton("👥 5", callback_data="link_temp_5"),
                InlineKeyboardButton("👥 10", callback_data="link_temp_10")
            ],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="link_main")]
        ]
        text = "🔢 چند نفر مجاز به استفاده از لینک باشند؟"
        return await fast_replace(query, text, kb)

    if data.startswith("link_temp_"):
        limit = int(data.split("_")[-1])
        try:
            link_obj: ChatInviteLink = await context.bot.create_chat_invite_link(
                chat_id,
                expire_date=datetime.utcnow() + timedelta(hours=24),
                member_limit=limit
            )
            store_link(link_obj.invite_link, {"type": "temp", "limit": limit, "expire": "24h"})
            text = f"🕒 لینک موقت ساخته شد:\n{link_obj.invite_link}\n\n⏳ اعتبار: ۲۴ ساعت\n👥 محدودیت: {limit} نفر"
        except Exception as e:
            text = f"⚠️ خطا در ساخت لینک موقت:\n<code>{e}</code>"

        kb = [[InlineKeyboardButton("🔙 بازگشت", callback_data="link_main")]]
        return await fast_replace(query, text, kb)

    # ========= بازگشت به منوی اصلی =========
    if data == "link_main":
        keyboard = generate_main_keyboard()
        text = get_panel_text()
        return await fast_replace(query, text, keyboard)

    # ========= بستن =========
    if data == "link_close":
        try:
            await query.message.delete()
        except:
            pass

# ===================== 🔤 توابع کمکی =====================
def generate_main_keyboard():
    return [
        [InlineKeyboardButton("📄 نمایش لینک", callback_data="link_show")],
        [InlineKeyboardButton("📤 ارسال به پیوی", callback_data="link_send_pm")],
        [InlineKeyboardButton("🔁 ساخت لینک جدید", callback_data="link_create_confirm")],
        [InlineKeyboardButton("🧾 ساخت لینک محدود", callback_data="link_temp_ask")],
        [InlineKeyboardButton("📚 راهنما", callback_data="link_help")],
        [InlineKeyboardButton("❌ بستن", callback_data="link_close")]
    ]

def get_panel_text():
    return "🔗 <b>پنل مدیریت لینک گروه</b>\n\nاز گزینه‌های زیر برای مشاهده، ساخت یا ارسال لینک استفاده کن."
