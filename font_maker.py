# ======================= 💎 خنگول فونت‌مستر 15.0 — Dual Edition =======================
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

    # تشخیص اینکه متن فارسیه یا لاتین
    if re.search(r"[a-zA-Z]", name):
        is_english = True
    else:
        is_english = False

    if is_english:
        result = generate_english_fonts(name)
    else:
        result = generate_persian_fonts(name)

    await update.message.reply_text(result["text"], parse_mode="HTML", reply_markup=result["keyboard"])
    return True


# 🎭 تولید فونت فارسی کشیده
def generate_persian_fonts(name):
    fonts = [
        f"⋯━━━ {name} ━━━⋯",
        f"───⋆⋅☆⋅⋆─── {name} ───⋆⋅☆⋅⋆───",
        f"╭━━━━━━━╯{name}╰━━━━━━━╮",
        f"╰═══〘 {name} 〙═══╯",
        f"═━┈┈ {name} ┈┈━═",
        f"✦━─━── {name} ───━─━✦",
        f"⋆｡°✩ {name} ✩°｡⋆",
        f"⋆⸙̩̩͙⊱ {name} ⊰⸙̩̩͙⋆",
        f"╔═══ஓ๑♡๑ஓ═══╗\n{name}\n╚═══ஓ๑♡๑ஓ═══╝",
        f"◈─── {name} ───◈",
        f"⋆˙⟡ {name} ⟡˙⋆",
        f"⋆⁺₊⋆ ☾ {name} ☽ ⋆⁺₊⋆",
        f"╔⧸⧹════ {name} ════⧸⧹╗",
        f"༺═── {name} ──═༻",
        f"❖── {name} ──❖",
        f"╭━─━─━─━ {name} ━─━─━─━╮",
        f"⋆━╍╍╍╍╍╍╍ {name} ╍╍╍╍╍╍╍━⋆",
        f"⋆★⋆ {name} ⋆★⋆",
        f"╭────────╮\n{name}\n╰────────╯",
        f"⋆───▣───⋆ {name} ⋆───▣───⋆",
    ]

    selected_fonts = random.sample(fonts, 10)
    text = f"<b>فونت‌های کشیده و خاص برای:</b> <i>{name}</i>\n\n"
    for i, style in enumerate(selected_fonts, start=1):
        text += f"{i}. <code>{style}</code>\n\n"

    text += "🔁 برای دیدن فونت‌های دیگر، روی دکمه زیر بزن."

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔁 فونت‌های جدید", callback_data=f"next_font:{name}")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="feature_back")]
    ])

    return {"text": text, "keyboard": keyboard}


# 💬 تولید فونت لاتین خاص و حرفه‌ای
def generate_english_fonts(name):
    # چند مدل از فونت‌های زیبا با حروف خاص یونیکد
    styles = [
        str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
                      "𝔄𝔅ℭ𝔇𝔈𝔉𝔊ℌℑ𝔍𝔎𝔏𝔐𝔑𝔒𝔓𝔔ℜ𝔖𝔗𝔘𝔙𝔚𝔛𝔜ℨ𝔞𝔟𝔠𝔡𝔢𝔣𝔤𝔥𝔦𝔧𝔨𝔩𝔪𝔫𝔬𝔭𝔮𝔯𝔰𝔱𝔲𝔳𝔴𝔵𝔶𝔷"),
        str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
                      "𝓐𝓑𝓒𝓓𝓔𝓕𝓖𝓗𝓘𝓙𝓚𝓛𝓜𝓝𝓞𝓟𝓠𝓡𝓢𝓣𝓤𝓥𝓦𝓧𝓨𝓩𝓪𝓫𝓬𝓭𝓮𝓯𝓰𝓱𝓲𝓳𝓴𝓵𝓶𝓷𝓸𝓹𝓺𝓻𝓼𝓽𝓾𝓿𝔀𝔁𝔂𝔃"),
        str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
                      "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇"),
        str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
                      "𝘈𝘉𝘊𝘋𝘌𝘍𝘎𝘏𝘐𝘑𝘒𝘓𝘔𝘕𝘖𝘗𝘘𝘙𝘚𝘛𝘜𝘝𝘞𝘟𝘠𝘡𝘢𝘣𝘤𝘥𝘦𝘧𝘨𝘩𝘪𝘫𝘬𝘭𝘮𝘯𝘰𝘱𝘲𝘳𝘴𝘵𝘶𝘷𝘸𝘹𝘺𝘻"),
        str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
                      "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ"),
        str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
                      "ᴬᴮᶜᴰᴱᶠᴳᴴᴵᴶᴷᴸᴹᴺᴼᴾᵠᴿˢᵗᵁⱽᵂˣʸᶻᵃᵇᶜᵈᵉᶠᵍʰᶦʲᵏˡᵐⁿᵒᵖᵠʳˢᵗᵘᵛʷˣʸᶻ"),
    ]

    # قاب‌های زیبا برای فونت انگلیسی
    frames = [
        lambda t: f"⋆── {t} ──⋆",
        lambda t: f"═── {t} ──═",
        lambda t: f"✦ {t} ✦",
        lambda t: f"⟨ {t} ⟩",
        lambda t: f"‹‹ {t} ››",
        lambda t: f"⌜ {t} ⌟",
        lambda t: f"⋆✧ {t} ✧⋆",
        lambda t: f"– {t} –",
        lambda t: f"⟦ {t} ⟧",
        lambda t: f"✎ {t}",
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


# 🔁 دکمه تولید فونت جدید (فارسی یا لاتین)
async def next_font(update, context):
    query = update.callback_query
    await query.answer()
    name = query.data.split(":")[1]

    if re.search(r"[a-zA-Z]", name):
        result = generate_english_fonts(name)
    else:
        result = generate_persian_fonts(name)

    await query.edit_message_text(result["text"], parse_mode="HTML", reply_markup=result["keyboard"])
