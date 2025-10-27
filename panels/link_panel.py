# panels/link_panel.py
import os, json, io
from datetime import datetime, timedelta
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatInviteLink, InputFile
)
from telegram.ext import ContextTypes
from PIL import Image, ImageDraw, ImageFont

# مسیر فایل گروه برای ذخیره لینک‌ها
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

# ساخت تصویر کارت لینک
def make_link_card(group_name, link, expire=None, limit=None):
    img = Image.new("RGB", (800, 400), (25, 25, 30))
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("arial.ttf", 40)
        font_text = ImageFont.truetype("arial.ttf", 28)
    except:
        font_title = font_text = ImageFont.load_default()

    draw.text((40, 50), "🔗 لینک گروه", fill="white", font=font_title)
    draw.text((40, 120), f"📛 گروه: {group_name}", fill="white", font=font_text)
    draw.text((40, 170), f"🌐 {link}", fill="#00ffcc", font=font_text)

    if expire or limit:
        draw.text((40, 230), "🕒 جزئیات لینک:", fill="white", font=font_text)
        if expire:
            draw.text((60, 270), f"⏳ اعتبار: {expire}", fill="#cccccc", font=font_text)
        if limit:
            draw.text((60, 310), f"👥 محدودیت عضو: {limit}", fill="#cccccc", font=font_text)

    draw.text((40, 360), f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}", fill="#888888", font=font_text)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


# ========================== پنل اصلی لینک ==========================
async def link_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]:
        return await update.message.reply_text("⚠️ این دستور فقط در گروه قابل استفاده است.")

    keyboard = [
        [InlineKeyboardButton("📄 نمایش لینک", callback_data="link_show")],
        [InlineKeyboardButton("🔁 ساخت لینک جدید", callback_data="link_create")],
        [InlineKeyboardButton("🧾 لینک موقت / محدود", callback_data="link_temp")],
        [InlineKeyboardButton("✉️ ارسال به پیوی", callback_data="link_send")],
        [InlineKeyboardButton("📚 راهنما", callback_data="link_help")],
        [InlineKeyboardButton("❌ بستن", callback_data="link_close")]
    ]
    text = (
        "🔗 <b>پنل مدیریت لینک گروه</b>\n\n"
        "از دکمه‌های زیر برای مشاهده یا ساخت لینک استفاده کنید.\n"
        "ربات باید ادمین باشد تا بتواند لینک واقعی بسازد."
    )
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")


# ========================== کنترل دکمه‌ها ==========================
async def link_panel_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    chat = query.message.chat
    chat_id = chat.id
    user = query.from_user

    gdata = load_group_data()
    group = gdata.setdefault(str(chat_id), {})

    def store_link(link, meta):
        group["invite"] = {
            "link": link,
            "created": datetime.now().isoformat(),
            "meta": meta
        }
        gdata[str(chat_id)] = group
        save_group_data(gdata)

    # ========= نمایش لینک =========
    if data == "link_show":
        inv = group.get("invite")
        if inv and inv.get("link"):
            link = inv["link"]
            meta = inv.get("meta", {})
        else:
            try:
                link = await context.bot.export_chat_invite_link(chat_id)
                meta = {"type": "default"}
                store_link(link, meta)
            except Exception as e:
                return await query.edit_message_text(
                    f"⚠️ ربات باید ادمین باشد تا لینک را بگیرد.\n\n<code>{e}</code>",
                    parse_mode="HTML"
                )

        card = make_link_card(chat.title, link, meta.get("expire"), meta.get("limit"))
        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت", callback_data="link_main")],
            [InlineKeyboardButton("❌ بستن", callback_data="link_close")]
        ]
        await query.message.delete()
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=InputFile(card, filename="link_card.png"),
            caption=f"🔗 لینک گروه:\n{link}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # ========= ساخت لینک جدید =========
    if data == "link_create":
        try:
            link_obj: ChatInviteLink = await context.bot.create_chat_invite_link(chat_id)
            store_link(link_obj.invite_link, {"type": "permanent"})
            link = link_obj.invite_link
        except Exception:
            link = await context.bot.export_chat_invite_link(chat_id)
            store_link(link, {"type": "fallback"})

        card = make_link_card(chat.title, link)
        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت", callback_data="link_main")],
            [InlineKeyboardButton("❌ بستن", callback_data="link_close")]
        ]
        await query.message.delete()
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=InputFile(card, filename="link_card.png"),
            caption=f"✅ لینک جدید ساخته شد:\n{link}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # ========= لینک موقت =========
    if data == "link_temp":
        try:
            link_obj: ChatInviteLink = await context.bot.create_chat_invite_link(
                chat_id,
                expire_date=datetime.utcnow() + timedelta(hours=24),
                member_limit=5
            )
            link = link_obj.invite_link
            store_link(link, {"type": "temp", "expire": "24h", "limit": 5})
            card = make_link_card(chat.title, link, "۲۴ ساعت", "۵ نفر")
        except Exception as e:
            return await query.edit_message_text(
                f"⚠️ خطا در ساخت لینک موقت:\n<code>{e}</code>",
                parse_mode="HTML"
            )

        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت", callback_data="link_main")],
            [InlineKeyboardButton("❌ بستن", callback_data="link_close")]
        ]
        await query.message.delete()
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=InputFile(card, filename="link_card.png"),
            caption=f"🕒 لینک موقت ساخته شد:\n{link}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # ========= ارسال لینک به پیوی =========
    if data == "link_send":
        inv = group.get("invite")
        if not inv or not inv.get("link"):
            try:
                link = await context.bot.export_chat_invite_link(chat_id)
                store_link(link, {"type": "default"})
            except Exception as e:
                return await query.edit_message_text(
                    f"⚠️ ربات باید ادمین باشد تا لینک را بگیرد.\n\n<code>{e}</code>",
                    parse_mode="HTML"
                )
        else:
            link = inv["link"]

        try:
            await context.bot.send_message(user.id, f"🔗 لینک گروه:\n{link}")
            text = "✅ لینک به پیوی شما ارسال شد."
        except:
            text = "⚠️ ابتدا به ربات پیام بده تا بتواند برایت بفرستد."

        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت", callback_data="link_main")],
            [InlineKeyboardButton("❌ بستن", callback_data="link_close")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # ========= راهنما =========
    if data == "link_help":
        text = (
            "📘 <b>راهنمای مدیریت لینک</b>\n\n"
            "• ربات باید ادمین باشد تا لینک واقعی بسازد.\n"
            "• لینک موقت بعد از ۲۴ ساعت یا ۵ عضو باطل می‌شود.\n"
            "• لینک‌ها در فایل group_control.json ذخیره می‌شوند.\n"
            "• اگر پیوی بسته باشد، ارسال لینک به شما ممکن نیست."
        )
        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت", callback_data="link_main")],
            [InlineKeyboardButton("❌ بستن", callback_data="link_close")]
        ]
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # ========= بازگشت به منوی اصلی =========
    if data == "link_main":
        keyboard = [
            [InlineKeyboardButton("📄 نمایش لینک", callback_data="link_show")],
            [InlineKeyboardButton("🔁 ساخت لینک جدید", callback_data="link_create")],
            [InlineKeyboardButton("🧾 لینک موقت / محدود", callback_data="link_temp")],
            [InlineKeyboardButton("✉️ ارسال به پیوی", callback_data="link_send")],
            [InlineKeyboardButton("📚 راهنما", callback_data="link_help")],
            [InlineKeyboardButton("❌ بستن", callback_data="link_close")]
        ]
        text = (
            "🔗 <b>پنل مدیریت لینک گروه</b>\n\n"
            "از دکمه‌های زیر برای مشاهده یا ساخت لینک استفاده کنید."
        )
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # ========= بستن =========
    if data == "link_close":
        try:
            await query.edit_message_text("❌ پنل لینک بسته شد.")
        except:
            pass
