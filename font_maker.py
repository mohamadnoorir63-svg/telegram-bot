import random
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters

ASK_NAME = 1

# ======================= 🎨 تابع اصلی =======================
async def font_maker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_type = update.effective_chat.type

    # جلوگیری از استفاده در گروه
    if chat_type in ["group", "supergroup"]:
        msg = await update.message.reply_text(
            "✨ لطفاً برای ساخت فونت، به پیوی ربات مراجعه کنید 🙏"
        )
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
async def receive_font_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    return await send_fonts(update, context, name)


# ======================= 💎 ارسال فونت‌ها =======================
async def send_fonts(update: Update, context: ContextTypes.DEFAULT_TYPE, name: str):
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
def generate_fonts(name: str):
    pre_groups = [
        ["𓄂",""𓃬","𓋥","𓄼","𓂀","𓅓"],
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
            "🅐🅑🅒🅓🅔🅕🅖🅗🅘🅙🅚🅛🅜🅝🅞🅟🅠🅡🅢🅣🅤🅥🅦🅧🅨🅩"
        )   "𝓐𝓑𝓒𝓓𝓔𝓕𝓖𝓗𝓘𝓙𝓚𝓛𝓜𝓝𝓞𝓟𝓠𝓡𝓢𝓣𝓤𝓥𝓦𝓧𝓨𝓩"
            "ⒶⒷⒸⒹⒺⒻⒼⒽⒾⒿⓀⓁⓂ️ⓃⓄⓅⓆⓇⓈⓉⓊⓋⓌⓍⓎⓏ"
            "🇦 🇧 🇨 🇩 🇪 🇫 🇬 🇭 🇮 🇯 🇰 🇱 🇲 🇳 🇴 🇵 🇶 🇷 🇸 🇹 🇺 🇻 🇼 🇽 🇾 🇿"
            "𝔸𝔹ℂ𝔻𝔼𝔽𝔾ℍ𝕀𝕁𝕂𝕃𝕄ℕ𝕆ℙℚℝ𝕊𝕋𝕌𝕍𝕎𝕏𝕐ℤ"
            "⒜⒝⒞⒟⒠⒡⒢⒣⒤⒥⒦⒧⒨⒩⒪⒫⒬⒭⒮⒯⒰⒱⒲⒳⒴⒵"
            "ⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙⓚⓛⓜⓝⓞⓟⓠⓡⓢⓣⓤⓥⓦⓧⓨⓩ"
            "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭"
    ]
    fonts = []

    while len(fonts) < 50:
        pre = "".join(random.choice(group) for group in pre_groups)
        post = "".join(random.choice(group) for group in post_groups)
        style = random.choice(unicode_styles)
        # ✅ بررسی طول قبل از maketrans
        if len(style[0]) != len(style[1]):
            continue
        uname = name.translate(str.maketrans(style[1], style[0]))
        fonts.append(f"{pre}{uname}{post}")

    return fonts


# ======================= 📄 ساخت صفحات =======================
def make_pages(name: str, fonts: list, page_size=10, max_pages=5):
    pages = []
    chunks = [fonts[i:i+page_size] for i in range(0, len(fonts), page_size)][:max_pages]
    for idx, chunk in enumerate(chunks):
        text = f"<b>↻ {name} ⇦</b>\n:• لیست فونت های پیشنهادی :\n"
        keyboard = []
        for i, style in enumerate(chunk, start=1):
            global_index = idx*page_size + (i-1)
            text += f"{i}- {style}\n"
            keyboard.append([InlineKeyboardButton(f"{i}- {style}", callback_data=f"send_font_{global_index}")])
        text += f"\n📄 صفحه {idx+1} از {len(chunks)}"

        nav = []
        if idx > 0: nav.append(InlineKeyboardButton("⬅️ قبلی", callback_data=f"prev_font_{idx-1}"))
        if idx < len(chunks)-1: nav.append(InlineKeyboardButton("➡️ بعدی", callback_data=f"next_font_{idx+1}"))
        if nav: keyboard.append(nav)
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="feature_back")])

        pages.append({"text": text, "keyboard": InlineKeyboardMarkup(keyboard)})
    return pages


# ======================= 📋 ارسال فونت انتخاب شده =======================
async def send_selected_font(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    font_id = int(query.data.replace("send_font_", ""))
    all_fonts = context.user_data.get("all_fonts", [])
    if 0 <= font_id < len(all_fonts):
        await query.message.reply_text(all_fonts[font_id])
    else:
        await query.message.reply_text("❗ فونت پیدا نشد.")


# ======================= 🔁 صفحات =======================
async def next_font(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    index = int(query.data.replace("next_font_", ""))
    pages = context.user_data.get("font_pages", [])
    if 0 <= index < len(pages):
        await query.edit_message_text(pages[index]["text"], parse_mode="HTML", reply_markup=pages[index]["keyboard"])


async def prev_font(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    index = int(query.data.replace("prev_font_", ""))
    pages = context.user_data.get("font_pages", [])
    if 0 <= index < len(pages):
        await query.edit_message_text(pages[index]["text"], parse_mode="HTML", reply_markup=pages[index]["keyboard"])


# ======================= 🎛 بازگشت به منوی اصلی =======================
# ======================= 🎛 بازگشت به منوی اصلی =======================
async def feature_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # حذف یا ویرایش پیام فعلی فونت
    try:
        await query.message.delete()
    except:
        pass

    # پایان ConversationHandler (اگه در حین ConversationHandler هستیم)
    return ConversationHandler.END
