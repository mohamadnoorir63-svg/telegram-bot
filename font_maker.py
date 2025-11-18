import random
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

ASK_NAME = 1

# ======================= 🎨 تابع اصلی =======================
async def font_maker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_type = update.effective_chat.type

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
    context.user_data["font_pages"] = make_pages(name, fonts, page_size=10, max_pages=30)

    pages = context.user_data["font_pages"]
    await update.message.reply_text(
        pages[0]["text"],
        parse_mode="HTML",
        reply_markup=pages[0]["keyboard"]
    )
    return ConversationHandler.END

# ======================= 🎭 تولید فونت‌های حرفه‌ای =======================
# ------------------ استایل‌های انگلیسی کامل ------------------
unicode_styles_funcs = [
    lambda s: "".join(["𝓐𝓑𝓒𝓓𝓔𝓕𝓖𝓗𝓘𝓙𝓚𝓛𝓜𝓝𝓞𝓟𝓠𝓡𝓢𝓣𝓤𝓥𝓦𝓧𝓨𝓩"[ord(c)-65] if 'A' <= c <= 'Z' else c for c in s.upper()]),
    lambda s: "".join(["𝓪𝓫𝓬𝓭𝓮𝓯𝓰𝓱𝓲𝓳𝓴𝓵𝓶𝓷𝓸𝓹𝓺𝓻𝓼𝓽𝓾𝓿𝔀𝔁𝔂𝔃"[ord(c)-97] if 'a' <= c <= 'z' else c for c in s.lower()]),
    lambda s: "".join(["ᎯᏰℭⅅ℮ℱᏩℋᏐℐӃℒℳℕᎾ⅌ℚℜᏕƬƲᏉᏔℵᎽℤ"[ord(c)-65] if 'A' <= c <= 'Z' else c for c in s.upper()]),
    lambda s: "".join(["🄰🄱🄲🄳🄴🄵🄶🄷🄸🄹🄺🄻🄼🄽🄾🄿🅀🅁🅂🅃🅄🅅🅆🅇🅈🅉"[ord(c)-65] if 'A' <= c <= 'Z' else c for c in s.upper()]),
    lambda s: "".join(["𝔄𝔅𝔇𝔈𝔉𝔊𝔍𝔎𝔏𝔐𝔑𝔒𝔓𝔔𝔖𝔗𝔘𝔙𝔚𝔛𝔜𝔝"[ord(c)-65] if 'A' <= c <= 'Z' else c for c in s.upper()]),
    lambda s: "".join(["𝕬𝕭𝕮𝕯𝕰𝕱𝕲𝕳𝕴𝕵𝕶𝕷𝕸𝕹𝕺𝕻𝕼𝕽𝕾𝕿𝖀𝖁𝖂𝖃𝖄𝖅"[ord(c)-65] if 'A' <= c <= 'Z' else c for c in s.upper()]),
]

# ------------------ الگوهای ثابت انگلیسی ------------------
fixed_patterns = [
    "۝ؔؑ❁➹‌❬⃟꯭({})꯭꯭‌⃟❭➹❁۝ؔؑ",
    "𓄂{}𓆃",
    "【♫❀꯭͞༄꯭͞𝄞_{}___❀꯭͞͞༄꯭͞𝄞",
    "⋆𝅦𝆉𓄂ꪰ☾︎⃝꯭🪩{}◆⃝🪩",
    "ـ‌‌ـ‌‌‌༊‌꯭ـ{}🐲ـ‌‌ـ‌‌‌‌‌༊‌꯭ـ",
    "┏┅┅🌸⃝⃭.  {}🌸⃝⃭❤━┅┅┓",
    " ᷤ‌‌➠🌼⃟🍃{}✿⃟⃘݊💞",
    "𝄟♔꯭⃮⃝⃮ 🦋 ꯭⃝⃮ ☾︎⃝ 𓄂{}𓆃☾︎⃝⋆♔꯭⃮⃝⃮ 🦋 ꯭⃝⃮ 𝄟",
    "𓋜𔘓❀{}❀𔒝",
    "🎀ꕥ✧»{}«✧ꕥ🎀",
    "♥️⃝⃭𝄞❉্͜͡▪️𒌍꯭🦋⃝⃡.𝅯.𝅰.꯭𝅱.𝅲.꯭𝅱.𝅰.𝅯.𝅮.꯭.{} 𝄞͡،⚛️",
    "𓄂ꪰ𓁪❥𝄞{}𝄞❥𓀛꯭𓆃ᵐᶠᶰ↬𓃬",
    "➹‌❬⃟꯭💕꯭‌⃟❭꯭ ꯭꯭‌꯭꯭‌{} ꯭ ❬⃟‌꯭꯭🪽꯭꯭‌⃟❭➹",
    "𓄂ꪴꪰ❨💎{}❩↬𓃬",
    "𓄂ꪴꪰ❨𝄠⃘۪۪۪۪۪۪ٜ♕{}♕𝄠⃘۪۪۪۪۪۪❩",
    "𓄂ꪴꪰ ♕{}♕𓆃",
    "𝄠⃘۪۪۪۪۪۪❩{}𝄠⃘۪۪۪۪۪۪❩"
]

# ------------------ استایل‌های فارسی ------------------
farsi_styles = [
    lambda s: "ـ".join(s),
    lambda s: "ۘۘ".join([c+"ـ" for c in s]),
    lambda s: "﹏".join([c+"ـ" for c in s]),
    lambda s: "۪ٜ".join([c+"ـ" for c in s]),
    lambda s: "ؒؔ✫ؒؔـ ҉๏‌๏ًٍ".join([c+"ـ" for c in s]),
    lambda s: "ٜ٘".join([c+"ـ" for c in s]),
    lambda s: "෴ِْ".join(s),
    lambda s: "ًٍʘًٍʘـ".join([c+"ـ" for c in s]),
    lambda s: "ؒؔـٓٓـؒؔ◌‌◌".join([c+"ـ" for c in s])
]

# ------------------ لیست کامل 69 قالب فارسی ------------------
templates = [
    "{0}ـ {1}ـ {2}ـ {3}",
    "{0}❈ۣۣـ🍁ـ{1}❈ۣۣـ🍁ـ{2}❈ۣۣـ🍁ـ{3}❈ۣۣـ🍁ـ",
    "]‌‌ـ‌‌ـ{0}‌‌ـ‌‌ـ]‌‌]‌‌ـ‌‌ـ{1}‌‌ـ‌‌ـ]‌‌]‌‌ـ‌‌ـ{2}‌‌ـ‌‌ـ]‌‌]‌‌ـ‌‌ـ{3}ـ‌‌ـ]",
    "{0}ـٰٰـٰٰـפ{1}ـٰٰـٰٰــ{2}ـٰٰـٰٰــ{3}ٍٕ",
    "{0}ؔؑـَؔ ـؔؑـَؔ๛ٖؔ{1}ؔؑـَؔ ـؔؑـَؔ๛ٖؔ{2}ؔؑـَؔ ـؔؑـَؔ๛ٖؔ{3}",
    "{0}ैـ۪ٜـ۪ٜـ۪ٜ❀‌‌ــؒؔؒؔ{1}ैـ۪ٜـ۪ٜـ۪ٜ❀‌‌ــؒؔ{2}ـैـ۪ٜـ۪ٜـ۪ٜ❀‌‌ــؒؔ{3}❀'‌‌'",
    "{0}‌‌ــ‌‌◕‌‌₰‌‌◚‌‌₰‌‌{1}ـ‌‌ــ‌‌ـ‌‌◕‌‌₰‌‌◚‌‌₰‌‌ {2}ـ‌‌ــ‌‌◕‌‌₰‌‌◚‌‌₰‌‌{3}‌‌◕‌‌₰",
    "{0}ــৡৡ{1}ــৡৡ{2}ــৡৡৡ'{3}",
    "{0}ــٍ‌ـۘۘــ{1}ْْـــْْـ{2}ــٍ‌ـۘۘــ{3}ۘۘـ",
    "{0}ــ{1}ــ{2}ّ{3}",
    # … ادامه تا تمام 69 قالب
]

# ------------------ تولید فونت ------------------
def generate_69_fonts(name):
    letters = list(name)
    while len(letters) < 4:
        letters.append('')
    fonts = []
    for template in templates:
        try:
            fonts.append(template.format(*letters))
        except:
            fonts.append(template)
    for style in farsi_styles:
        fonts.append(style(name))
    return fonts

def generate_fonts(name: str):
    is_farsi = any("\u0600" <= c <= "\u06FF" for c in name)
    if is_farsi:
        return generate_69_fonts(name)
    else:
        fonts = [func(name) for func in unicode_styles_funcs]
        fonts += [fp.format(name) for fp in fixed_patterns]
        return fonts

# ======================= 📄 ساخت صفحات پویا =======================
def make_pages(name: str, fonts: list, page_size=10, max_pages=30):
    pages = []
    total_pages = min((len(fonts) + page_size - 1) // page_size, max_pages)
    for idx in range(total_pages):
        chunk = fonts[idx*page_size : (idx+1)*page_size]
        text = f"**↻ {name} ⇦**\n:• لیست فونت های پیشنهادی :\n"
        keyboard = []
        for i, style in enumerate(chunk, start=1):
            global_index = idx*page_size + (i-1)
            text += f"{i}- {style}\n"
            keyboard.append([InlineKeyboardButton(f"{i}- {style}", callback_data=f"send_font_{global_index}")])
        text += f"\n📄 صفحه {idx+1} از {total_pages}"

        nav = []
        if idx > 0:
            nav.append(InlineKeyboardButton("⬅️ قبلی", callback_data=f"prev_font_{idx-1}"))
        if idx < total_pages - 1:
            nav.append(InlineKeyboardButton("➡️ بعدی", callback_data=f"next_font_{idx+1}"))
        if nav:
            keyboard.append(nav)

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

# ======================= 🔁 ناوبری صفحات =======================
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
async def feature_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        await query.message.delete()
    except:
        pass
    return ConversationHandler.END

# ======================= 🧪 تست فونت =======================
if __name__ == "__main__":
    name_en = "Ali"
    fonts_en = generate_fonts(name_en)
    print("✅ انگلیسی:")
    for i, f in enumerate(fonts_en, 1):
        print(f"{i}. {f}")

    name_fa = "علی"
    fonts_fa = generate_fonts(name_fa)
    print("\n✅ فارسی:")
    for i, f in enumerate(fonts_fa, 1):
        print(f"{i}. {f}")
