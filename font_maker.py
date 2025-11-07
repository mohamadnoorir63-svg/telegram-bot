import asyncio
import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

ASK_NAME = 1  # مرحله‌ی پرسیدن اسم

# 🎨 تابع اصلی تولید فونت
async def font_maker(update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_type = update.effective_chat.type

    if chat_type in ["group", "supergroup"]:
        msg = await update.message.reply_text("✨ برای ساخت فونت، لطفاً به پیوی ربات مراجعه کنید 🙏")
        await asyncio.sleep(6)
        try:
            await msg.delete()
            await update.message.delete()
        except Exception as e:
            if "message to be replied not found" not in str(e).lower():
                print(f"⚠️ خطا در حذف پیام: {e}")
        return ConversationHandler.END

    if text.strip() == "فونت":
        await update.message.reply_text("🌸 چه اسمی رو برات فونت کنم؟")
        return ASK_NAME

    if text.startswith("فونت "):
        name = text.replace("فونت", "").strip()
        return await send_fonts(update, context, name)

    return ConversationHandler.END

async def receive_font_name(update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if not name:
        await update.message.reply_text("❗ لطفاً یه اسم بنویس تا فونت بسازم.")
        return ASK_NAME

    return await send_fonts(update, context, name)

async def send_fonts(update, context, name):
    is_english = bool(re.search(r"[a-zA-Z]", name))
    fonts = generate_english_fonts(name) if is_english else generate_persian_fonts(name)

    await update.message.reply_text(
        fonts[0]["text"],
        parse_mode="HTML",
        reply_markup=fonts[0]["keyboard"]
    )

    context.user_data["font_pages"] = fonts
    context.user_data["font_index"] = 0
    return ConversationHandler.END

# ======================= 🎭 تولید فونت فارسی جذاب =======================
def generate_persian_fonts(name):
    styles = [
        f"♡﹏﹏﹏ {name} ﹏﹏﹏♡", f"╭──❀──╮ {name} ╰──❀──╯", f"♡•́‿•̀♡ {name} ♡•́‿•̀♡",
        f"💞 {name} 💞", f"❣️ {name} ❣️", f"꧁༺♥༻꧂ {name} ꧁༺♥༻꧂",
        f"💋 {name} 💋", f"✿♡✿ {name} ✿♡✿", f"🌸 {name} 🌸", f"⋆˙⟡♡⟡˙⋆ {name} ⋆˙⟡♡⟡˙⋆",
        f"╭────────╮\n{name}\n╰────────╯", f"✧˚༺ {name} ༻˚✧", f"♡₊˚ {name} ˚₊♡", f"❀❀ {name} ❀❀",
        f"⟡♡ {name} ♡⟡", f"✿•₊˚ {name} ˚₊•✿", f"⊹✿⊹ {name} ⊹✿⊹"
    ]
    return make_pages(name, styles)

# ======================= ✨ تولید فونت انگلیسی جذاب و چندصفحه‌ای =======================
def generate_english_fonts(name):
    fancy_fonts = [
        "𝓐𝓑𝓒𝓓𝓔𝓕𝓖𝓗𝓘𝓙𝓚𝓛𝓜𝓝𝓞𝓟𝓠𝓡𝓢𝓣𝓤𝓥𝓦𝓧𝓨𝓩",
        "𝔄𝔅ℭ𝔇𝔈𝔉𝔊ℌℑ𝔍𝔎𝔏𝔐𝔑𝔒𝔓𝔔ℜ𝔖𝔗𝔘𝔙𝔚𝔛𝔜ℨ",
        "𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙",
        "𝓜𝓸𝓱𝓪𝓶𝓶𝓪𝓭", "𝑀𝑜ℎ𝒶𝓂𝓂𝒶𝓭", "𝙈𝙤𝙝𝙖𝙢𝙢𝙖𝙙"
    ]

    styles = []
    symbols = ["•", "✦", "⋆", "✿", "♡", "☾", "❖", "⟡", "❋", "⊰", "✧", "⚡", "🔥", "💫", "✨", "♛", "♚"]

    # ترکیب فونت و علامت‌ها
    for f in fancy_fonts:
        styled = ''.join([f.get(c, c) if isinstance(f, dict) else c for c in name])
        for s in symbols:
            styles.append(f"{s} {styled} {s}")
    
    return make_pages(name, styles)

# ======================= 📄 تقسیم فونت‌ها به صفحات =======================
def make_pages(name, all_fonts, page_size=10):
    pages = []
    chunks = [all_fonts[i:i + page_size] for i in range(0, len(all_fonts), page_size)]

    for idx, chunk in enumerate(chunks):
        text = f"<b>🎨 فونت‌های خاص و تزئینی برای:</b> <i>{name}</i>\n\n"
        for i, style in enumerate(chunk, start=1):
            text += f"{i}. <code>{style}</code>\n"
        text += f"\n📄 صفحه {idx + 1} از {len(chunks)}"

        nav_buttons = []
        if idx > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ قبلی", callback_data=f"prev_font:{idx - 1}"))
        if idx < len(chunks) - 1:
            nav_buttons.append(InlineKeyboardButton("➡️ بعدی", callback_data=f"next_font:{idx + 1}"))

        pages.append({
            "text": text,
            "keyboard": InlineKeyboardMarkup([
                nav_buttons,
                [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="feature_back")]
            ])
        })
    return pages

# ======================= 🔁 کنترل صفحات فونت =======================
async def next_font(update, context):
    query = update.callback_query
    await query.answer()
    index = int(query.data.split(":")[1])
    fonts = context.user_data.get("font_pages", [])
    if 0 <= index < len(fonts):
        await query.edit_message_text(
            fonts[index]["text"],
            parse_mode="HTML",
            reply_markup=fonts[index]["keyboard"]
        )

async def prev_font(update, context):
    query = update.callback_query
    await query.answer()
    index = int(query.data.split(":")[1])
    fonts = context.user_data.get("font_pages", [])
    if 0 <= index < len(fonts):
        await query.edit_message_text(
            fonts[index]["text"],
            parse_mode="HTML",
            reply_markup=fonts[index]["keyboard"]
        )
