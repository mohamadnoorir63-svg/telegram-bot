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

# ⚡ تابع سریع برای جایگزینی پیام
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
    chat_id = str(chat.id)

    gdata = load_group_data()
    group = gdata.setdefault(chat_id, {})
    lang = group.get("lang", "fa")

    # ========= تغییر زبان =========
    if data in ["lang_fa", "lang_en", "lang_de"]:
        lang = data.replace("lang_", "")
        group["lang"] = lang
        gdata[chat_id] = group
        save_group_data(gdata)

        # پنل جدید با زبان انتخاب‌شده نمایش داده می‌شود
        keyboard = generate_main_keyboard(lang)
        text = get_panel_text(lang)
        return await fast_replace(query, text, keyboard)

    # ========= بقیه بخش‌ها =========
    if data == "link_show":
        inv = group.get("invite")
        if inv and inv.get("link"):
            text = get_text(lang, "current_link") + f"\n\n{inv['link']}"
        else:
            try:
                link = await context.bot.export_chat_invite_link(chat_id)
                group["invite"] = {"link": link, "created": datetime.now().isoformat()}
                gdata[chat_id] = group
                save_group_data(gdata)
                text = get_text(lang, "new_link") + f"\n{link}"
            except Exception as e:
                text = get_text(lang, "bot_admin_error") + f"\n\n<code>{e}</code>"

        kb = [[InlineKeyboardButton(get_text(lang, "back"), callback_data="link_main")]]
        return await fast_replace(query, text, kb)

    if data == "link_create_confirm":
        kb = [
            [InlineKeyboardButton(get_text(lang, "yes"), callback_data="link_create_yes")],
            [InlineKeyboardButton(get_text(lang, "no"), callback_data="link_main")]
        ]
        return await fast_replace(query, get_text(lang, "confirm_text"), kb)

    if data == "link_create_yes":
        try:
            link_obj: ChatInviteLink = await context.bot.create_chat_invite_link(chat_id)
            group["invite"] = {"link": link_obj.invite_link, "created": datetime.now().isoformat()}
            gdata[chat_id] = group
            save_group_data(gdata)
            text = get_text(lang, "new_link") + f"\n{link_obj.invite_link}"
        except Exception:
            link = await context.bot.export_chat_invite_link(chat_id)
            group["invite"] = {"link": link, "created": datetime.now().isoformat()}
            gdata[chat_id] = group
            save_group_data(gdata)
            text = get_text(lang, "new_link") + f"\n{link}"

        kb = [[InlineKeyboardButton(get_text(lang, "back"), callback_data="link_main")]]
        return await fast_replace(query, text, kb)

    if data == "link_temp_ask":
        kb = [
            [
                InlineKeyboardButton("👥 1", callback_data="link_temp_1"),
                InlineKeyboardButton("👥 5", callback_data="link_temp_5"),
                InlineKeyboardButton("👥 10", callback_data="link_temp_10")
            ],
            [InlineKeyboardButton(get_text(lang, "back"), callback_data="link_main")]
        ]
        return await fast_replace(query, get_text(lang, "ask_limit"), kb)

    if data.startswith("link_temp_"):
        limit = int(data.split("_")[-1])
        try:
            link_obj: ChatInviteLink = await context.bot.create_chat_invite_link(
                chat.id,
                expire_date=datetime.utcnow() + timedelta(hours=24),
                member_limit=limit
            )
            group["invite"] = {"link": link_obj.invite_link, "created": datetime.now().isoformat()}
            gdata[chat_id] = group
            save_group_data(gdata)
            text = get_text(lang, "temp_link").format(link=link_obj.invite_link, limit=limit)
        except Exception as e:
            text = get_text(lang, "temp_error").format(e=e)

        kb = [[InlineKeyboardButton(get_text(lang, "back"), callback_data="link_main")]]
        return await fast_replace(query, text, kb)

    if data == "link_help":
        text = get_text(lang, "help")
        kb = [[InlineKeyboardButton(get_text(lang, "back"), callback_data="link_main")]]
        return await fast_replace(query, text, kb)

    if data == "link_main":
        keyboard = generate_main_keyboard(lang)
        text = get_panel_text(lang)
        return await fast_replace(query, text, keyboard)

    if data == "link_close":
        try:
            await query.message.delete()
        except:
            pass


# ===================== 🔤 ترجمه‌ها =====================
def generate_main_keyboard(lang):
    return [
        [
            InlineKeyboardButton("🇮🇷🇦🇫 فارسی", callback_data="lang_fa"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
            InlineKeyboardButton("🇩🇪 Deutsch", callback_data="lang_de")
        ],
        [InlineKeyboardButton(get_text(lang, "show_link"), callback_data="link_show")],
        [InlineKeyboardButton(get_text(lang, "create_link"), callback_data="link_create_confirm")],
        [InlineKeyboardButton(get_text(lang, "temp_button"), callback_data="link_temp_ask")],
        [InlineKeyboardButton(get_text(lang, "help_btn"), callback_data="link_help")],
        [InlineKeyboardButton(get_text(lang, "close_btn"), callback_data="link_close")]
    ]


def get_panel_text(lang):
    texts = {
        "fa": "🔗 <b>پنل مدیریت لینک گروه</b>\n\nاز گزینه‌های زیر استفاده کن 👇",
        "en": "🔗 <b>Group Link Panel</b>\n\nUse the buttons below to manage group links 👇",
        "de": "🔗 <b>Gruppenlink-Panel</b>\n\nVerwende die folgenden Schaltflächen 👇"
    }
    return texts.get(lang, texts["fa"])


def get_text(lang, key):
    data = {
        "show_link": {"fa": "📄 نمایش لینک", "en": "📄 Show Link", "de": "📄 Link anzeigen"},
        "create_link": {"fa": "🔁 ساخت لینک جدید", "en": "🔁 Create New Link", "de": "🔁 Neuen Link erstellen"},
        "temp_button": {"fa": "🧾 ساخت لینک محدود", "en": "🧾 Temporary Link", "de": "🧾 Temporärer Link"},
        "help_btn": {"fa": "📚 راهنما", "en": "📚 Help", "de": "📚 Hilfe"},
        "close_btn": {"fa": "❌ بستن", "en": "❌ Close", "de": "❌ Schließen"},
        "back": {"fa": "🔙 بازگشت", "en": "🔙 Back", "de": "🔙 Zurück"},
        "yes": {"fa": "✅ بله", "en": "✅ Yes", "de": "✅ Ja"},
        "no": {"fa": "❌ خیر", "en": "❌ No", "de": "❌ Nein"},
        "confirm_text": {
            "fa": "آیا مطمئنی می‌خوای لینک جدید بسازی؟ لینک قبلی فعال می‌مونه.",
            "en": "Are you sure you want to create a new link? The old one remains active.",
            "de": "Möchtest du wirklich einen neuen Link erstellen? Der alte bleibt aktiv."
        },
        "current_link": {"fa": "🔗 لینک فعلی گروه:", "en": "🔗 Current group link:", "de": "🔗 Aktueller Gruppenlink:"},
        "new_link": {"fa": "✅ لینک جدید ساخته شد:", "en": "✅ New link created:", "de": "✅ Neuer Link erstellt:"},
        "bot_admin_error": {
            "fa": "⚠️ ربات باید ادمین باشد تا لینک را بگیرد.",
            "en": "⚠️ Bot must be admin to get link.",
            "de": "⚠️ Der Bot muss Admin sein, um den Link zu erhalten."
        },
        "ask_limit": {
            "fa": "چند نفر مجاز به استفاده از لینک باشند؟",
            "en": "How many people can use this link?",
            "de": "Wie viele Personen dürfen den Link verwenden?"
        },
        "temp_link": {
            "fa": "🕒 لینک موقت ساخته شد:\n{link}\n\n⏳ اعتبار: ۲۴ ساعت\n👥 محدودیت: {limit} نفر",
            "en": "🕒 Temporary link created:\n{link}\n\n⏳ Valid: 24h\n👥 Limit: {limit} users",
            "de": "🕒 Temporärer Link erstellt:\n{link}\n\n⏳ Gültig: 24h\n👥 Limit: {limit} Personen"
        },
        "temp_error": {
            "fa": "⚠️ خطا در ساخت لینک:\n<code>{e}</code>",
            "en": "⚠️ Error creating link:\n<code>{e}</code>",
            "de": "⚠️ Fehler beim Erstellen des Links:\n<code>{e}</code>"
        },
        "help": {
            "fa": "📘 <b>راهنمای لینک‌ها</b>\n• ربات باید ادمین باشد.\n• لینک موقت پس از ۲۴ ساعت منقضی می‌شود.",
            "en": "📘 <b>Link Help</b>\n• Bot must be admin.\n• Temporary links expire after 24h.",
            "de": "📘 <b>Link-Hilfe</b>\n• Der Bot muss Admin sein.\n• Temporäre Links laufen nach 24h ab."
        }
    }
    return data[key].get(lang, data[key]["fa"])
