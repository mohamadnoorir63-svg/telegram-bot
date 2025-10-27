# panels/link_panel.py
import os, json
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatInviteLink
from telegram.ext import ContextTypes

# 📂 مسیر فایل داده گروه‌ها
GROUP_CTRL_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "group_control.json")

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
    if chat.type not in ["group", "supergroup"]:
        return await update.message.reply_text("⚠️ فقط در گروه قابل استفاده است.")

    gdata = load_group_data()
    group = gdata.setdefault(str(chat.id), {})
    lang = group.get("lang", "fa")

    keyboard = generate_main_keyboard(lang)
    text = get_panel_text(lang)
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")


# ===================== ⚙️ کنترل دکمه‌ها =====================
async def link_panel_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    chat = query.message.chat
    chat_id = chat.id
    user = query.from_user

    gdata = load_group_data()
    group = gdata.setdefault(str(chat_id), {})
    lang = group.get("lang", "fa")

    def store_link(link, meta):
        group["invite"] = {"link": link, "created": datetime.now().isoformat(), "meta": meta}
        gdata[str(chat_id)] = group
        save_group_data(gdata)

    # ========= تغییر زبان =========
    if data == "link_toggle_lang":
        new_lang = "en" if lang == "fa" else "fa"
        group["lang"] = new_lang
        gdata[str(chat_id)] = group
        save_group_data(gdata)
        keyboard = generate_main_keyboard(new_lang)
        text = get_panel_text(new_lang)
        return await fast_replace(query, text, keyboard)

    # ========= نمایش لینک =========
    if data == "link_show":
        inv = group.get("invite")
        if inv and inv.get("link"):
            text = f"🔗 <b>{'Group Link' if lang == 'en' else 'لینک فعلی گروه'}:</b>\n\n{inv['link']}"
        else:
            try:
                link = await context.bot.export_chat_invite_link(chat_id)
                store_link(link, {"type": "default"})
                text = f"✅ {'New link created:' if lang == 'en' else 'لینک جدید ساخته شد:'}\n{link}"
            except Exception as e:
                text = f"⚠️ {'Bot must be admin to get link.' if lang == 'en' else 'ربات باید ادمین باشد تا لینک را بگیرد.'}\n\n<code>{e}</code>"

        kb = [[InlineKeyboardButton("🔙 Back" if lang == "en" else "🔙 بازگشت", callback_data="link_main")]]
        return await fast_replace(query, text, kb)

    # ========= ساخت لینک دائمی =========
    if data == "link_create_confirm":
        kb = [
            [InlineKeyboardButton("✅ Yes, create" if lang == "en" else "✅ بله، بساز", callback_data="link_create_yes")],
            [InlineKeyboardButton("❌ Cancel" if lang == "en" else "❌ خیر، انصراف", callback_data="link_main")]
        ]
        text = (
            "Are you sure you want to create a new permanent link?\n\nOld link remains active."
            if lang == "en"
            else "آیا مطمئنی می‌خوای یک لینک جدید (دائمی) بسازی؟\n\nلینک قبلی همچنان فعال می‌مونه."
        )
        return await fast_replace(query, text, kb)

    if data == "link_create_yes":
        try:
            link_obj: ChatInviteLink = await context.bot.create_chat_invite_link(chat_id)
            store_link(link_obj.invite_link, {"type": "permanent"})
            text = f"✅ {'New link created:' if lang == 'en' else 'لینک جدید ساخته شد:'}\n{link_obj.invite_link}"
        except Exception:
            link = await context.bot.export_chat_invite_link(chat_id)
            store_link(link, {"type": "fallback"})
            text = f"✅ {'New link created:' if lang == 'en' else 'لینک جدید ساخته شد:'}\n{link}"

        kb = [[InlineKeyboardButton("🔙 Back" if lang == "en" else "🔙 بازگشت", callback_data="link_main")]]
        return await fast_replace(query, text, kb)

    # ========= ساخت لینک محدود =========
    if data == "link_temp_ask":
        kb = [
            [
                InlineKeyboardButton("👥 1", callback_data="link_temp_1"),
                InlineKeyboardButton("👥 5", callback_data="link_temp_5"),
                InlineKeyboardButton("👥 10", callback_data="link_temp_10")
            ],
            [InlineKeyboardButton("🔙 Back" if lang == "en" else "🔙 بازگشت", callback_data="link_main")]
        ]
        text = "How many people can use this link?" if lang == "en" else "🔢 چند نفر مجاز به استفاده از لینک باشند؟"
        return await fast_replace(query, text, kb)

    # ========= لینک محدود انتخابی =========
    if data.startswith("link_temp_"):
        limit = int(data.split("_")[-1])
        try:
            link_obj: ChatInviteLink = await context.bot.create_chat_invite_link(
                chat_id,
                expire_date=datetime.utcnow() + timedelta(hours=24),
                member_limit=limit
            )
            store_link(link_obj.invite_link, {"type": "temp", "limit": limit, "expire": "24h"})
            text = (
                f"🕒 Temporary link created:\n{link_obj.invite_link}\n\n⏳ Expire: 24h\n👥 Limit: {limit}"
                if lang == "en"
                else f"🕒 لینک موقت ساخته شد:\n{link_obj.invite_link}\n\n⏳ اعتبار: ۲۴ ساعت\n👥 محدودیت: {limit} نفر"
            )
        except Exception as e:
            text = f"⚠️ Error creating link:\n<code>{e}</code>" if lang == "en" else f"⚠️ خطا در ساخت لینک موقت:\n<code>{e}</code>"

        kb = [[InlineKeyboardButton("🔙 Back" if lang == "en" else "🔙 بازگشت", callback_data="link_main")]]
        return await fast_replace(query, text, kb)

    # ========= راهنما =========
    if data == "link_help":
        text = (
            "📘 <b>Link Help</b>\n\n"
            "• Bot must be admin to create real links.\n"
            "• Temporary links expire after 24h or limited members.\n"
            "• To receive link in PM, you must start the bot first."
            if lang == "en"
            else "📘 <b>راهنمای لینک‌ها</b>\n\n• ساخت لینک جدید فقط برای مدیران مجاز است.\n• لینک موقت پس از ۲۴ ساعت یا تعداد مشخص منقضی می‌شود.\n• برای ارسال به پیوی، ابتدا باید به ربات پیام دهید."
        )
        kb = [[InlineKeyboardButton("🔙 Back" if lang == "en" else "🔙 بازگشت", callback_data="link_main")]]
        return await fast_replace(query, text, kb)

    # ========= بازگشت به منوی اصلی =========
    if data == "link_main":
        keyboard = generate_main_keyboard(lang)
        text = get_panel_text(lang)
        return await fast_replace(query, text, keyboard)

    # ========= بستن =========
    if data == "link_close":
        try:
            await query.message.delete()
        except:
            pass


# ===================== 🔤 توابع کمکی زبان =====================
def generate_main_keyboard(lang):
    if lang == "en":
        return [
            [InlineKeyboardButton("🇮🇷 Switch to Persian", callback_data="link_toggle_lang")],
            [InlineKeyboardButton("📄 Show Link", callback_data="link_show")],
            [InlineKeyboardButton("🔁 Create New Link", callback_data="link_create_confirm")],
            [InlineKeyboardButton("🧾 Temporary Link", callback_data="link_temp_ask")],
            [InlineKeyboardButton("📚 Help", callback_data="link_help")],
            [InlineKeyboardButton("❌ Close", callback_data="link_close")]
        ]
    else:
        return [
            [InlineKeyboardButton("🇬🇧 English Version", callback_data="link_toggle_lang")],
            [InlineKeyboardButton("📄 نمایش لینک", callback_data="link_show")],
            [InlineKeyboardButton("🔁 ساخت لینک جدید", callback_data="link_create_confirm")],
            [InlineKeyboardButton("🧾 ساخت لینک محدود", callback_data="link_temp_ask")],
            [InlineKeyboardButton("📚 راهنما", callback_data="link_help")],
            [InlineKeyboardButton("❌ بستن", callback_data="link_close")]
        ]


def get_panel_text(lang):
    return (
        "🔗 <b>Group Link Panel</b>\n\nUse the buttons below to manage group links."
        if lang == "en"
        else "🔗 <b>پنل مدیریت لینک گروه</b>\n\nاز گزینه‌های زیر برای مشاهده، ساخت یا ارسال لینک استفاده کن."
    )
