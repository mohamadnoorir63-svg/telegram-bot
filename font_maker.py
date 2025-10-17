# ======================= 💎 Khenqol FontMaster 27.0 — Persian & English Hybrid Edition =======================
import random
import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# 🎨 تابع اصلی ساخت فونت
async def font_maker(update, context):
    text = update.message.text.strip()
    if not text.startswith("فونت "):
        return False

    name = text.replace("فونت", "").strip()
    if not name:
        return await update.message.reply_text("🖋 بعد از «فونت»، نام خودت رو بنویس تا فونت‌هات ساخته بشن.")

    # تشخیص فارسی یا انگلیسی
    is_english = bool(re.search(r"[a-zA-Z]", name))
    result = generate_english_fonts(name) if is_english else generate_persian_fonts(name)

    await update.message.reply_text(result["text"], parse_mode="HTML", reply_markup=result["keyboard"])
    return True


# ======================= 🏵 فونت فارسی =======================
def generate_persian_fonts(name):
    # طرح‌های خاص با خطوط تراز شده و یک‌خطی
    fonts = [
        f"═─── {name} ───═",
        f"⋆── {name} ──⋆",
        f"╭────── {name} ──────╮",
        f"╰═════ {name} ═════╯",
        f"⋆━──── {name} ────━⋆",
        f"┈┈┈⋆ {name} ⋆┈┈┈",
        f"⋆✶ {name} ✶⋆",
        f"✦─━─━─ {name} ━─━─━✦",
        f"⋆✧ {name} ✧⋆",
        f"═══⊹⊱ {name} ⊰⊹═══",
        f"⋆⸙̩̩͙⊱ {name} ⊰⸙̩̩͙⋆",
        f"⋆⁺₊⋆ {name} ⋆₊⁺⋆",
        f"╔═── {name} ──═╗",
        f"◈── {name} ──◈",
        f"⋆━── {name} ──━⋆",
        f"╰── {name} ──╯",
        f"╭━━━ {name} ━━━╮",
        f"⋆⁺˚ {name} ˚⁺⋆",
        f"═╬═ {name} ═╬═",
        f"⋆˙⟡ {name} ⟡˙⋆",
        f"⋆✦ {name} ✦⋆",
        f"═╬═══ {name} ═══╬═",
        f"⋆━━ {name} ━━⋆",
        f"─━─ {name} ─━─",
        f"═• {name} •═",
        f"⋆═── {name} ───═⋆",
        f"━⋆━ {name} ━⋆━",
        f"═━━═ {name} ═━━═",
        f"⟪ {name} ⟫",
        f"⋆•° {name} °•⋆",
        f"═──═ {name} ═──═",
        f"⋆══ {name} ══⋆",
        f"⋆˙⋆ {name} ⋆˙⋆",
        f"⋆╰── {name} ──╯⋆",
        f"⋆╭── {name} ──╮⋆",
        f"═╬═ {name} ╬═",
        f"⋆═╬═ {name} ╬═⋆",
        f"╭──═ {name} ═──╮",
        f"╰──═ {name} ═──╯",
        f"═══ {name} ═══",
        f"⋆──── {name} ────⋆",
        f"━⋆══ {name} ══⋆━",
        f"⋆──═ {name} ═──⋆",
        f"⋆══ {name} ══⋆",
        f"═──⋆ {name} ⋆──═",
        f"⋆═══ {name} ═══⋆",
        f"═──⋆ {name} ⋆──═",
        f"═━━⋆ {name} ⋆━━═",
        f"⋆──━ {name} ━──⋆",
        f"═⋆═ {name} ═⋆═",
        f"⋆═ {name} ═⋆",
        f"═⋆══ {name} ══⋆═",
        f"⋆═══ {name} ═══⋆",
        f"═━═ {name} ═━═",
        f"⋆═══ {name} ═══⋆",
        f"⋆━── {name} ──━⋆",
        f"═━═ {name} ═━═",
        f"⋆━══ {name} ═━⋆",
        f"════ {name} ════",
        f"═⋆── {name} ──⋆═",
        f"⋆═──═ {name} ═──═⋆",
        f"⋆═━═ {name} ═━═⋆",
        f"⋆━━═ {name} ═━━⋆",
        f"⋆━═══ {name} ═══━⋆",
        f"═⋆═──═ {name} ═──═⋆═",
        f"⋆═━──━═ {name} ═━──━═⋆",
        f"═╬═══ {name} ═══╬═",
        f"⋆═══╬═══ {name} ═══╬═══⋆",
        f"⋆═╬═──═╬═ {name} ╬═──═╬═⋆",
        f"═⋆═══⋆═ {name} ═⋆═══⋆═",
        f"⋆═══╬═══ {name} ═══╬═══⋆",
        f"⋆━━╬━━ {name} ━━╬━━⋆",
        f"═⋆══╬══⋆═ {name} ═⋆══╬══⋆═",
        f"⋆═╬═╬═ {name} ╬═╬═╬═⋆",
        f"═╬═╬═╬═ {name} ╬═╬═╬═╬═",
        f"⋆═══⋆═══ {name} ═══⋆═══⋆",
        f"═━━⋆═══ {name} ═══⋆━━═",
        f"⋆━╬═══╬━ {name} ━╬═══╬━⋆",
    ]

    selected_fonts = random.sample(fonts, 10)
    text = f"<b>فونت‌های خاص برای:</b> <i>{name}</i>\n\n"
    for i, style in enumerate(selected_fonts, start=1):
        text += f"{i}. <code>{style}</code>\n\n"
    text += "🔁 برای دیدن فونت‌های دیگر، روی دکمه زیر بزن."

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔁 فونت‌های جدید", callback_data=f"next_font:{name}")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="feature_back")]
    ])

    return {"text": text, "keyboard": keyboard}


# ======================= ✨ فونت انگلیسی =======================
def generate_english_fonts(name):
    styles = [
        str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
                      "𝓐𝓑𝓒𝓓𝓔𝓕𝓖𝓗𝓘𝓙𝓚𝓛𝓜𝓝𝓞𝓟𝓠𝓡𝓢𝓣𝓤𝓥𝓦𝓧𝓨𝓩𝓪𝓫𝓬𝓭𝓮𝓯𝓰𝓱𝓲𝓳𝓴𝓵𝓶𝓷𝓸𝓹𝓺𝓻𝓼𝓽𝓾𝓿𝔀𝔁𝔂𝔃"),
        str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
                      "𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳"),
        str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
                      "𝘈𝘉𝘊𝘋𝘌𝘍𝘎𝘏𝘐𝘑𝘒𝘓𝘔𝘕𝘖𝘗𝘘𝘙𝘚𝘛𝘜𝘝𝘞𝘟𝘠𝘡𝘢𝘣𝘤𝘥𝘦𝘧𝘨𝘩𝘪𝘫𝘬𝘭𝘮𝘯𝘰𝘱𝘲𝘳𝘴𝘵𝘶𝘷𝘸𝘹𝘺𝘻"),
        str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
                      "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘵𝘶𝘷𝘄𝘅𝘆𝘇"),
        str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
                      "🅰🅱🅲🅳🅴🅵🅶🅷🅸🅹🅺🅻🅼🅽🅾🅿🆀🆁🆂🆃🆄🆅🆆🆇🆈🆉🅰🅱🅲🅳🅴🅵🅶🅷🅸🅹🅺🅻🅼🅽🅾🅿🆀🆁🆂🆃🆄🆅🆆🆇🆈🆉"),
    ]

    frames = [
        lambda t: f"═── {t} ──═",
        lambda t: f"⋆━── {t} ──━⋆",
        lambda t: f"⋆✦ {t} ✦⋆",
        lambda t: f"═╬═ {t} ╬═",
        lambda t: f"⋆═──═ {t} ═──═⋆",
        lambda t: f"━⋆━ {t} ━⋆━",
        lambda t: f"⋆━━ {t} ━━⋆",
        lambda t: f"⟪ {t} ⟫",
        lambda t: f"⋆═══ {t} ═══⋆",
        lambda t: f"═━━═ {t} ═━━═",
    ]

    results = []
    for _ in range(10):
        style = random.choice(styles)
        framed = random.choice(frames)
        results.append(framed(name.translate(style)))

    text = f"<b>Stylish Fonts for:</b> <i>{name}</i>\n\n"
    for i, style in enumerate(results, start=1):
        text += f"{i}. <code>{style}</code>\n\n"

    text += "🔁 Click the button below for more fonts."

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔁 New Fonts", callback_data=f"next_font:{name}")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="feature_back")]
    ])

    return {"text": text, "keyboard": keyboard}


# ======================= 🔁 دکمه تولید مجدد =======================
async def next_font(update, context):
    query = update.callback_query
    await query.answer()
    name = query.data.split(":")[1]
    is_english = bool(re.search(r"[a-zA-Z]", name))
    result = generate_english_fonts(name) if is_english else generate_persian_fonts(name)
    await query.edit_message_text(result["text"], parse_mode="HTML", reply_markup=result["keyboard"])
