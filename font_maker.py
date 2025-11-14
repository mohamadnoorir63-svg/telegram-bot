import random
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

ASK_NAME = 1

# ======================= 🎨 تابع اصلی =======================
async def font_maker(update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_type = update.effective_chat.type

    if chat_type in ["group", "supergroup"]:
        msg = await update.message.reply_text("✨ لطفاً برای ساخت فونت، به پیوی ربات مراجعه کنید 🙏")
        await asyncio.sleep(6)
        try:
            await msg.delete()
            await update.message.delete()
        except:
            pass
        return ConversationHandler.END

    if text == "فونت":
        await update.message.reply_text("🌸 چه اسمی رو برات فونت کنم؟")
        return ASK_NAME

    if text.startswith("فونت "):
        name = text.replace("فونت", "").strip()
        return await send_fonts(update, context, name)

    return ConversationHandler.END

# ======================= 🌸 دریافت اسم =======================
async def receive_font_name(update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    return await send_fonts(update, context, name)

# ======================= 💎 ارسال فونت‌ها =======================
async def send_fonts(update, context, name):
    fonts = generate_fonts(name)

    context.user_data["all_fonts"] = fonts
    context.user_data["font_pages"] = make_pages(name, fonts, 10, 5)

    pages = context.user_data["font_pages"]

    await update.message.reply_text(
        pages[0]["text"],
        parse_mode="HTML",
        reply_markup=pages[0]["keyboard"]
    )

    return ConversationHandler.END

# ======================= 🎭 تولید فونت‌های شیک =======================
def generate_fonts(name):
    pre_groups = [
        ["𓄂","𓆃","𓃬","𓋥","𓄼","𓂀","𓅓"],
        ["ꪰ","ꪴ","𝄠","𝅔","꧁","꧂","ꕥ"],
        ["⚝","☬","☾","☽","★","✦","✧"]
    ]

    post_groups = [
        ["✿","♡","❖","░","❋","☯","❂"],
        ["✧","✦","❂","★","✺","✶","✸"],
        ["⋆","⟡","❋","•","✾","✢","✤"]
    ]

    unicode_styles = [
        (
            "𝓐𝓑𝓒𝓓𝓔𝓕𝓖𝓗𝓘𝓙𝓚𝓛𝓜𝓝𝓞𝓟𝓠𝓡𝓢𝓣𝓤𝓥𝓦𝓧𝓨𝓩"
            "𝓪𝓫𝓬𝓭𝓮𝓯𝓰𝓱𝓲𝓳𝓴𝓵𝓶𝓷𝓸𝓹𝓺𝓻𝓼𝓽𝓾𝓿𝔀𝔁𝔂𝔃",
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        ),
        (
            "🄰🄱🄲🄳🄴🄵🄶🄷🄸🄹🄺🄻🄼🄽🄾🄿🅀🅁🅂🅃🅄🅅🅆🅇🅈🅉"
            "🄰🄱🄲🄳🄴🄵🄶🄷🄸🄹🄺🄻🄼🄽🄾🄿🅀🅁🅂🅃🅄🅅🅆🅇🅈🅉",
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        )
    ]

    fonts = []

    for _ in range(50):
        pre = "".join(random.choice(group) for group in pre_groups)
        post = "".join(random.choice(group) for group in post_groups)

        style = random.choice(unicode_styles)
        uname = name.translate(str.maketrans(style[1], style[0]))

        fonts.append(f"{pre}{uname}{post}")

    return fonts

# ======================= 📄 ساخت صفحات =======================
def make_pages(name, fonts, page_size=10, max_pages=5):
    pages = []
    total_chunks = [fonts[i:i + page_size] for i in range(0, len(fonts), page_size)]
    total_chunks = total_chunks[:max_pages]

    for page_index, chunk in enumerate(total_chunks):
        text = f"<b>↻ {name} ⇦</b>\n:• لیست فونت های پیشنهادی :\n"

        # فقط لیست فونت‌ها بدون دکمه کپی
        for i, style in enumerate(chunk, start=1):
            text += f"{i}- {style}\n"

        text += f"\n📄 صفحه {page_index + 1} از {len(total_chunks)}"

        keyboard = []
        nav = []

        if page_index > 0:
            nav.append(InlineKeyboardButton("⬅️ قبلی", callback_data=f"prev_font_{page_index - 1}"))
        if page_index < len(total_chunks) - 1:
            nav.append(InlineKeyboardButton("➡️ بعدی", callback_data=f"next_font_{page_index + 1}"))

        if nav:
            keyboard.append(nav)

        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="feature_back")])

        pages.append({
            "text": text,
            "keyboard": InlineKeyboardMarkup(keyboard)
        })

    return pages

# ======================= 🔁 صفحات =======================
async def next_font(update, context):
    q = update.callback_query
    await q.answer()

    index = int(q.data.replace("next_font_", ""))
    pages = context.user_data["font_pages"]

    await q.edit_message_text(
        pages[index]["text"],
        parse_mode="HTML",
        reply_markup=pages[index]["keyboard"]
    )

async def prev_font(update, context):
    q = update.callback_query
    await q.answer()

    index = int(q.data.replace("prev_font_", ""))
    pages = context.user_data["font_pages"]

    await q.edit_message_text(
        pages[index]["text"],
        parse_mode="HTML",
        reply_markup=pages[index]["keyboard"]
    )
