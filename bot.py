# ======================= 📦 وارد کردن ماژول‌های اصلی =======================
import os
import json
import random
import asyncio
import zipfile
import shutil
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

# ======================= ⚙️ تنظیمات اولیه =======================
ADMIN_ID = 7089376754  # آیدی عددی مدیر اصلی
TOKEN = os.getenv("BOT_TOKEN")  # توکن از متغیر محیطی
if not TOKEN:
    raise Exception("❌ متغیر BOT_TOKEN تنظیم نشده است!")

# ======================= 🤖 کنترل احساس و لحن =======================
def detect_emotion(text: str) -> str:
    """تشخیص احساس متن بر اساس کلمات کلیدی ساده"""
    text = text.lower()
    if any(word in text for word in ["غم", "دلگیر", "ناراحت", "گریه", "بدحال"]):
        return "sad"
    elif any(word in text for word in ["خوشحال", "شاد", "خنده", "عالی", "خوبه"]):
        return "happy"
    elif any(word in text for word in ["عصبانی", "دیوانه", "حرص", "ناراحت شدم"]):
        return "angry"
    elif any(word in text for word in ["دوستت دارم", "عشق", "دلم برات تنگ شده"]):
        return "love"
    else:
        return "neutral"

def enhance_sentence(sentence: str) -> str:
    """زیباسازی جمله‌های ساده با ایموجی و احساس"""
    emotion_map = {
        "sad": ["😔", "💭", "🕊️"],
        "happy": ["😄", "🌈", "✨"],
        "angry": ["😤", "🔥", "💢"],
        "love": ["❤️", "🥰", "💞"],
        "neutral": ["🙂", "🤖"]
    }
    emotion = detect_emotion(sentence)
    if emotion in emotion_map:
        return sentence + " " + random.choice(emotion_map[emotion])
    if len(sentence) < 5:
        return sentence + " 🙂"
    return sentence + " " + random.choice(["🤖", "😄", "🌸", "🪄", "✨"])

# ======================= 💬 ریپلی مود و پاسخ ثابت =======================
def should_reply(update) -> bool:
    """بررسی می‌کند آیا ربات باید پاسخ بدهد یا نه"""
    global status
    if not status.get("active", True):
        shadow_learn(update.message.text, "")
        return False
    if status.get("reply_mode", False):
        return bool(update.message.reply_to_message and update.message.reply_to_message.from_user.is_bot)
    return True

async def replymode_special(update, context):
    """پاسخ مخصوص در حالت ریپلی"""
    if not status.get("reply_mode", False):
        return False
    text = update.message.text.strip().lower()
    if "خنگول کجایی" in text:
        await update.message.reply_text("اینجام 😌 فقط وقتی با ریپلای صدام کنی جواب می‌دم 💬")
        return True
    return False

# ======================= 🧠 پاسخ هوشمند ساده =======================
def smart_response(text: str, user_id: int = None) -> str:
    """پاسخ پیش‌فرض زمانی که جمله در حافظه نیست"""
    t = text.lower()
    generic_replies = [
        "جالبه 😄",
        "بیشتر بگو 🤔",
        "واقعاً؟ 😯",
        "خب که اینطور 😌",
        "آهان... ادامه بده 🙂",
        "تو همیشه چیزای خاصی می‌گی 😄",
        "درسته... ادامه بده 🤖"
    ]
    emotional_responses = {
        "sad": ["غمگین نباش 💙", "همه‌چی درست میشه 🌧️", "آغوش مجازی برات 🤗"],
        "happy": ["خوشحالم خوشحالی 😄", "شاد باش همیشه 🌈", "زندگی قشنگه ✨"],
        "angry": ["آروم باش 😤", "نفس عمیق بکش 😮‍💨", "حرص نخور رفیق 😅"],
        "love": ["منم دوستت دارم 😳", "عشق یعنی تو ❤️", "خجالت نکش 😌💞"]
    }
    mood = detect_emotion(t)
    if mood in emotional_responses:
        return random.choice(emotional_responses[mood])
    if t.strip().endswith("?") or "؟" in t:
        return random.choice([
            "سؤال خوبیه 🤔",
            "به نظرم جوابش پیچیده‌ست 😅",
            "ممم، شاید... شاید هم نه 😌"
        ])
    return random.choice(generic_replies)

# ======================= 💞 حافظه احساس کاربر =======================
emotion_memory = {}

def remember_emotion(user_id: int, emotion: str):
    """ذخیره آخرین احساس کاربر"""
    emotion_memory[user_id] = {
        "emotion": emotion,
        "time": datetime.now().isoformat()
    }

def get_last_emotion(user_id: int):
    """آخرین احساس ثبت‌شده کاربر"""
    return emotion_memory.get(user_id, {}).get("emotion", None)

def emotion_context_reply(current_emotion: str, last_emotion: str):
    """پاسخ بر اساس تغییر احساس"""
    if not last_emotion or current_emotion == last_emotion:
        return None
    if last_emotion == "sad" and current_emotion == "happy":
        return "خوشحالم حالت بهتر شده 🌤️"
    if last_emotion == "happy" and current_emotion == "sad":
        return "چی شد که ناراحت شدی؟ 💭"
    if last_emotion == "angry" and current_emotion == "love":
        return "عجب تغییر مثبتی 😍"
    return None

# ======================= ⚙️ وضعیت عمومی =======================
status = {
    "active": True,
    "learning": True,
    "welcome": True,
    "locked": False,
    "reply_mode": False,
    "mode": "نرمال"
}
STATUS_FILE = "status.json"

def save_status():
    """ذخیره وضعیت ربات"""
    tmp = STATUS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)
    os.replace(tmp, STATUS_FILE)

def load_status():
    """بارگذاری وضعیت"""
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                status.update(saved)
        except json.JSONDecodeError:
            print("[WARN] فایل status.json خراب بود، بازنشانی شد.")
            save_status()
load_status()
# ======================= 🧠 مدیریت حافظه و فایل‌های داده =======================
def init_files():
    """بررسی و ایجاد فایل‌های اصلی حافظه در صورت نبود"""
    required_files = [
        "memory.json",
        "group_data.json",
        "jokes.json",
        "fortunes.json"
    ]
    for file in required_files:
        if not os.path.exists(file) or os.path.getsize(file) == 0:
            with open(file, "w", encoding="utf-8") as f:
                f.write("{}")
    print("✅ فایل‌های حافظه بررسی و ایجاد شدند.")

def load_data(filename: str):
    """خواندن داده از فایل JSON"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] خواندن فایل {filename} ناموفق بود: {e}")
        return {}

def save_data(filename: str, data):
    """ذخیره داده در فایل JSON (ایمن با tmp)"""
    try:
        tmp = filename + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, filename)
    except Exception as e:
        print(f"[ERROR] ذخیره فایل {filename} ناموفق بود:", e)

# ======================= ☁️ بک‌آپ خودکار =======================
async def auto_backup(bot):
    """بک‌آپ خودکار هر ۱۲ ساعت"""
    while True:
        await asyncio.sleep(43200)  # 12 ساعت
        try:
            await cloudsync_internal(bot, "Auto Backup")
        except Exception as e:
            print(f"[AUTO BACKUP ERROR] {e}")

# ======================= 📦 فیلتر فایل‌های مهم =======================
def _should_include_in_backup(path: str) -> bool:
    """انتخاب فایل‌هایی که در بک‌آپ ذخیره می‌شوند"""
    lowered = path.lower()
    skip_dirs = ["__pycache__", ".git", "venv", "restore_temp"]
    if any(sd in lowered for sd in skip_dirs):
        return False
    if lowered.endswith(".zip") or os.path.basename(lowered).startswith("backup_"):
        return False
    return lowered.endswith((".json", ".jpg", ".png", ".webp", ".mp3", ".ogg", ".txt", ".py"))

# ======================= ☁️ بک‌آپ ابری =======================
async def cloudsync_internal(bot, reason="Manual Backup"):
    """ایجاد و ارسال فایل ZIP بک‌آپ به ادمین"""
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"backup_{now}.zip"
    try:
        with zipfile.ZipFile(filename, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
            base = os.path.dirname(__file__)
            for root, _, files in os.walk(base):
                for file in files:
                    full_path = os.path.join(root, file)
                    if _should_include_in_backup(full_path):
                        arcname = os.path.relpath(full_path, base)
                        zipf.write(full_path, arcname=arcname)
        with open(filename, "rb") as f:
            await bot.send_document(chat_id=ADMIN_ID, document=f, filename=filename)
        await bot.send_message(chat_id=ADMIN_ID, text=f"☁️ {reason} انجام شد ✅")
    except Exception as e:
        print(f"[CLOUD BACKUP ERROR] {e}")
        try:
            await bot.send_message(chat_id=ADMIN_ID, text=f"⚠️ خطا در Cloud Backup:\n{e}")
        except:
            pass
    finally:
        if os.path.exists(filename):
            os.remove(filename)

# ======================= ☁️ دستور بک‌آپ دستی =======================
async def cloudsync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اجرای بک‌آپ ابری دستی"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")
    await cloudsync_internal(context.bot, "Manual Cloud Backup")

# ======================= 💾 بک‌آپ دستی و محلی =======================
async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ایجاد فایل ZIP و ارسال در چت فعلی"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه بک‌آپ بگیره!")
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"backup_{now}.zip"
    try:
        with zipfile.ZipFile(filename, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
            base = os.path.dirname(__file__)
            for root, _, files in os.walk(base):
                for file in files:
                    full_path = os.path.join(root, file)
                    if _should_include_in_backup(full_path):
                        arcname = os.path.relpath(full_path, base)
                        zipf.write(full_path, arcname=arcname)
        with open(filename, "rb") as f:
            await update.message.reply_document(document=f, filename=filename)
        await update.message.reply_text("✅ بک‌آپ کامل گرفته شد!")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در گرفتن بک‌آپ:\n{e}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

# ======================= 🔁 بازیابی بک‌آپ =======================
async def restore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع فرآیند بازیابی بک‌آپ"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")
    await update.message.reply_text("📂 لطفاً فایل ZIP بک‌آپ را ارسال کن تا بازیابی شود.")
    context.user_data["await_restore"] = True

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت فایل ZIP و بازیابی ایمن آن"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")
    if not context.user_data.get("await_restore"):
        return
    doc = update.message.document
    if not doc or not doc.file_name.lower().endswith(".zip"):
        return await update.message.reply_text("❗ لطفاً یک فایل ZIP معتبر بفرست.")
    restore_zip = "restore.zip"
    restore_dir = "restore_temp"
    try:
        tg_file = await doc.get_file()
        await tg_file.download_to_drive(restore_zip)
        if os.path.exists(restore_dir):
            shutil.rmtree(restore_dir)
        os.makedirs(restore_dir, exist_ok=True)

        with zipfile.ZipFile(restore_zip, "r") as zip_ref:
            for member in zip_ref.namelist():
                member_path = os.path.abspath(os.path.join(restore_dir, member))
                if not member_path.startswith(os.path.abspath(restore_dir)):
                    raise Exception("⚠️ Zip path traversal detected!")
            zip_ref.extractall(restore_dir)

        important_files = [f for f in os.listdir(restore_dir) if f.endswith(".json")]
        moved_any = False
        for fname in important_files:
            src = os.path.join(restore_dir, fname)
            if os.path.exists(src):
                shutil.move(src, fname)
                moved_any = True

        if moved_any:
            await update.message.reply_text("✅ بازیابی کامل انجام شد!")
        else:
            await update.message.reply_text("ℹ️ هیچ فایلی برای جایگزینی پیدا نشد. ZIP را بررسی کن.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در بازیابی:\n{e}")
    finally:
        if os.path.exists(restore_zip):
            os.remove(restore_zip)
        if os.path.exists(restore_dir):
            shutil.rmtree(restore_dir)
        context.user_data["await_restore"] = False
import random
from telegram import Update
from telegram.ext import ContextTypes

# ======================= 📘 یادگیری خودکار و دستی =======================
def learn(phrase, *responses):
    """یادگیری دستی: جمله + چند پاسخ"""
    data = load_data("memory.json")
    phrases = data.get("phrases", {})
    phrase = phrase.strip()
    if phrase not in phrases:
        phrases[phrase] = []
    for resp in responses:
        if resp not in phrases[phrase]:
            phrases[phrase].append(resp)
    data["phrases"] = phrases
    save_data("memory.json", data)
    return f"✅ جمله '{phrase}' با {len(responses)} پاسخ جدید یاد گرفته شد!"

def shadow_learn(phrase, response):
    """یادگیری در حالت خاموشی (بدون پاسخ‌گویی)"""
    if not phrase.strip():
        return
    data = load_data("memory.json")
    phrases = data.get("phrases", {})
    if phrase not in phrases:
        phrases[phrase] = [response] if response else []
        data["phrases"] = phrases
        save_data("memory.json", data)

def auto_learn_from_text(text):
    """یادگیری خودکار از مکالمات عمومی"""
    if not text or len(text) < 4:
        return
    data = load_data("memory.json")
    phrases = data.get("phrases", {})
    if text not in phrases:
        phrases[text] = []
        data["phrases"] = phrases
        save_data("memory.json", data)

def get_reply(text):
    """پیدا کردن پاسخ از حافظه"""
    data = load_data("memory.json")
    phrases = data.get("phrases", {})
    for key, replies in phrases.items():
        if key in text:
            return random.choice(replies) if replies else None
    return None

# ======================= 😂 جوک و 🔮 فال =======================
def save_joke(update: Update):
    """ثبت جوک با ریپلای"""
    replied = update.message.reply_to_message
    if not replied:
        return
    data = load_data("jokes.json")
    joke_id = str(len(data) + 1)
    if replied.text:
        data[joke_id] = {"type": "text", "value": replied.text}
    elif replied.photo:
        file_id = replied.photo[-1].file_id
        data[joke_id] = {"type": "photo", "value": file_id}
    elif replied.video:
        data[joke_id] = {"type": "video", "value": replied.video.file_id}
    elif replied.sticker:
        data[joke_id] = {"type": "sticker", "value": replied.sticker.file_id}
    save_data("jokes.json", data)
    return update.message.reply_text("😂 جوک جدید ذخیره شد!")

def save_fortune(update: Update):
    """ثبت فال با ریپلای"""
    replied = update.message.reply_to_message
    if not replied:
        return
    data = load_data("fortunes.json")
    fortune_id = str(len(data) + 1)
    if replied.text:
        data[fortune_id] = {"type": "text", "value": replied.text}
    elif replied.photo:
        data[fortune_id] = {"type": "photo", "value": replied.photo[-1].file_id}
    elif replied.video:
        data[fortune_id] = {"type": "video", "value": replied.video.file_id}
    elif replied.sticker:
        data[fortune_id] = {"type": "sticker", "value": replied.sticker.file_id}
    save_data("fortunes.json", data)
    return update.message.reply_text("🔮 فال جدید ذخیره شد!")

async def list_jokes(update: Update):
    """لیست همه جوک‌ها"""
    data = load_data("jokes.json")
    if not data:
        return await update.message.reply_text("📂 هیچ جوکی ثبت نشده 😅")
    msg = "\n".join([f"{k}. {v.get('value', '')[:40]}..." for k, v in data.items()])
    await update.message.reply_text("😂 لیست جوک‌ها:\n" + msg)

async def list_fortunes(update: Update):
    """لیست همه فال‌ها"""
    data = load_data("fortunes.json")
    if not data:
        return await update.message.reply_text("📂 هیچ فالی ثبت نشده 😔")
    msg = "\n".join([f"{k}. {v.get('value', '')[:40]}..." for k, v in data.items()])
    await update.message.reply_text("🔮 لیست فال‌ها:\n" + msg)

# ======================= 🧮 محاسبه درصد هوش =======================
async def show_intelligence(update: Update):
    """محاسبه درصد هوش بر اساس داده‌ها"""
    score = 0
    details = []

    # 🧠 حافظه
    if os.path.exists("memory.json"):
        data = load_data("memory.json")
        phrases = len(data.get("phrases", {}))
        responses = sum(len(v) for v in data.get("phrases", {}).values()) if phrases else 0
        if phrases > 50 and responses > 100:
            score += 40
            details.append("🧠 حافظه گسترده و فعال ✅")
        elif phrases > 15:
            score += 25
            details.append("🧩 حافظه متوسط و مفید 🟢")
        else:
            score += 10
            details.append("⚪ حافظه محدود ولی در حال رشد")

    # 😂 شوخ‌طبعی
    if os.path.exists("jokes.json"):
        data = load_data("jokes.json")
        count = len(data)
        if count > 20:
            score += 20
            details.append("😂 شوخ‌طبع و باحال 😎")
        elif count > 5:
            score += 10
            details.append("😅 کمی شوخ‌طبع 🟢")

    # 🔮 خلاقیت
    if os.path.exists("fortunes.json"):
        data = load_data("fortunes.json")
        count = len(data)
        if count > 10:
            score += 10
            details.append("🔮 خلاقیت بالا ✨")

    # 👥 هوش اجتماعی
    if os.path.exists("group_data.json"):
        data = load_data("group_data.json")
        groups = data.get("groups", [])
        gcount = len(groups) if isinstance(groups, list) else len(data.get("groups", {}))
        if gcount > 5:
            score += 15
            details.append("👥 اجتماعی و فعال 📈")

    # ❤️ احساس
    user_id = update.effective_user.id
    last_emotion = get_last_emotion(user_id)
    if last_emotion:
        score += 5
        details.append(f"💞 احساس اخیر تشخیص داده شده: {last_emotion}")

    total = min(100, score)
    msg = (
        f"🧠 درصد هوش خنگول: {total}%\n\n" +
        "\n".join(details) +
        "\n\n🌟 وضعیت: " +
        ("🚀 نابغه خلاق و اجتماعی" if total >= 80 else
         "💡 باهوش و رشد‌یابنده" if total >= 50 else
         "🐣 در مسیر یادگیری")
    )
    await update.message.reply_text(msg)

# ======================= 🪄 تولید جمله تصادفی =======================
def generate_sentence():
    """ساخت جمله تصادفی از حافظه"""
    data = load_data("memory.json")
    phrases = list(data.get("phrases", {}).keys())
    if not phrases:
        return "هنوز چیزی یاد نگرفتم 😅"
    phrase = random.choice(phrases)
    responses = data.get("phrases", {}).get(phrase, [])
    if responses:
        return random.choice(responses)
    return phrase
# ======================= 📨 ارسال همگانی (Broadcast) =======================
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال پیام همگانی ایمن به تمام کاربران و گروه‌ها (فقط مدیر اصلی)"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")

    msg = " ".join(context.args)
    if not msg:
        return await update.message.reply_text("❗ بعد از /broadcast پیام را بنویس.")

    memory_data = load_data("memory.json")
    users = memory_data.get("users", [])
    groups_data = load_data("group_data.json").get("groups", {})

    group_ids = []
    if isinstance(groups_data, dict):
        group_ids = list(groups_data.keys())
    elif isinstance(groups_data, list):
        group_ids = [g.get("id") for g in groups_data if "id" in g]

    sent, failed = 0, 0
    await update.message.reply_text("🚀 ارسال پیام همگانی در حال انجام است...")

    # ارسال با فاصله برای جلوگیری از FloodWait
    for uid in users:
        try:
            await context.bot.send_message(chat_id=int(uid), text=msg)
            sent += 1
            await asyncio.sleep(0.1)
        except Exception as e:
            failed += 1
            if "Too Many Requests" in str(e):
                await asyncio.sleep(3)

    for gid in group_ids:
        try:
            await context.bot.send_message(chat_id=int(gid), text=msg)
            sent += 1
            await asyncio.sleep(0.15)
        except Exception as e:
            failed += 1
            if "Too Many Requests" in str(e):
                await asyncio.sleep(3)

    await update.message.reply_text(
        f"📨 ارسال همگانی انجام شد ✅\n"
        f"👤 کاربران: {len(users)} | 👥 گروه‌ها: {len(group_ids)}\n"
        f"✅ موفق: {sent} | ⚠️ ناموفق: {failed}"
    )

# ======================= 📈 آمار کامل گروه‌ها (Fullstats) =======================
async def fullstats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آمار کامل گروه‌ها به صورت ایمن (فقط مدیر اصلی)"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")

    try:
        data = load_data("group_data.json")
        groups = data.get("groups", {})

        if not groups:
            return await update.message.reply_text("ℹ️ هنوز هیچ گروهی ثبت نشده.")

        text = "📈 <b>آمار کامل گروه‌ها:</b>\n\n"
        count = 0
        if isinstance(groups, list):
            groups_list = groups
        else:
            groups_list = [{"id": gid, **info} for gid, info in groups.items()]

        for g in groups_list:
            count += 1
            group_id = g.get("id", "نامشخص")
            title = g.get("title", f"Group_{group_id}")
            members = len(g.get("members", []))
            last_active = g.get("last_active", "نامشخص")

            try:
                chat = await context.bot.get_chat(group_id)
                if chat.title:
                    title = chat.title
            except Exception:
                pass

            text += (
                f"🏠 <b>{title}</b>\n"
                f"👥 اعضا: {members}\n"
                f"🕓 آخرین فعالیت: {last_active}\n"
                "━━━━━━━━━━━━━━━\n"
            )

            if count % 10 == 0:
                await asyncio.sleep(0.5)

        if len(text) > 3900:
            text = text[:3900] + "\n... (لیست کوتاه شد)"

        await update.message.reply_html(text)

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در آمار گروه‌ها:\n{e}")
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)
import aiofiles

HELP_FILE = "custom_help.txt"

# ======================= 👋 خوشامدگویی با عکس پروفایل =======================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال پیام خوش‌آمد زیبا با عکس پروفایل"""
    if not status.get("welcome", True):
        return
    for member in update.message.new_chat_members:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        text = (
            f"🎉 خوش اومدی {member.first_name}!\n"
            f"📅 تاریخ ورود: {now}\n"
            f"🏠 گروه: {update.message.chat.title}\n"
            f"🌈 امیدوارم لحظات خوبی اینجا داشته باشی!"
        )
        try:
            photos = await context.bot.get_user_profile_photos(member.id, limit=1)
            if photos.total_count > 0:
                file_id = photos.photos[0][-1].file_id
                await update.message.reply_photo(file_id, caption=text)
            else:
                await update.message.reply_text(text)
        except Exception:
            await update.message.reply_text(text)

# ======================= 📊 آمار کلی ربات (فقط مدیر اصلی) =======================
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آمار خلاصه"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")
    data = load_data("memory.json")
    phrases = len(data.get("phrases", {}))
    responses = sum(len(v) for v in data.get("phrases", {}).values()) if phrases else 0
    groups_data = load_data("group_data.json")
    groups = groups_data.get("groups", {})
    group_count = len(groups) if isinstance(groups, dict) else len(groups)
    users = len(data.get("users", []))
    mode = status.get("mode", "نرمال")
    msg = (
        "📊 <b>آمار خنگول ابری:</b>\n\n"
        f"👤 کاربران ثبت‌شده: <b>{users}</b>\n"
        f"👥 گروه‌های فعال: <b>{group_count}</b>\n"
        f"🧩 جمله‌های یادگرفته‌شده: <b>{phrases}</b>\n"
        f"💬 پاسخ‌های ذخیره‌شده: <b>{responses}</b>\n"
        f"🎭 مود فعلی: <b>{mode}</b>\n"
        f"☁️ نسخه فعال: <b>8.6.2 Cloud+ Fusion Ultra AI+</b>"
    )
    await update.message.reply_html(msg)

# ======================= 🧹 ریست و ریلود حافظه =======================
async def reset_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پاکسازی کامل داده‌ها"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")
    for f in ["memory.json", "group_data.json", "jokes.json", "fortunes.json"]:
        if os.path.exists(f):
            os.remove(f)
    init_files()
    await update.message.reply_text("🧹 تمام داده‌ها با موفقیت پاک شدند!")

async def reload_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بارگذاری مجدد حافظه"""
    init_files()
    await update.message.reply_text("🔄 حافظه دوباره بارگذاری شد!")

# ======================= 🚪 خروج از گروه =======================
async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور خروج از گروه"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")
    await update.message.reply_text("🫡 خدافظ! تا دیدار بعدی 😂")
    await context.bot.leave_chat(update.message.chat.id)

# ======================= 📘 راهنمای قابل ویرایش =======================
async def show_custom_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش فایل راهنما"""
    if not os.path.exists(HELP_FILE):
        return await update.message.reply_text(
            "ℹ️ هنوز هیچ متنی برای راهنما ثبت نشده.\n"
            "مدیر اصلی می‌تونه با ریپلای و نوشتن «ثبت راهنما» تنظیمش کنه."
        )
    async with aiofiles.open(HELP_FILE, "r", encoding="utf-8") as f:
        text = await f.read()
    await update.message.reply_text(text)

async def save_custom_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ثبت راهنمای جدید با ریپلای — فقط مدیر اصلی"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")
    if not update.message.reply_to_message or not update.message.reply_to_message.text:
        return await update.message.reply_text("❗ باید روی یک پیام متنی ریپلای کنی!")
    text = update.message.reply_to_message.text
    async with aiofiles.open(HELP_FILE, "w", encoding="utf-8") as f:
        await f.write(text)
    await update.message.reply_text("✅ متن راهنما ذخیره شد!")

# ======================= ✳️ استارت اولیه =======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش پیام خوش‌آمد"""
    await update.message.reply_text(
        "🤖 خنگول فارسی 8.6.2 Cloud+ Fusion Ultra AI+ آماده به خدمت است!\n"
        "📘 برای دیدن لیست دستورات بنویس: راهنما"
    )

async def notify_admin_on_startup(app):
    """ارسال پیام فعال‌سازی به ادمین هنگام استارت"""
    try:
        await app.bot.send_message(chat_id=ADMIN_ID, text="🚀 خنگول ابری فعال شد ✅")
        print("[INFO] Startup notification sent ✅")
    except Exception as e:
        print(f"[ERROR] Admin notify failed: {e}")

# ======================= ⚙️ مدیریت خطاها =======================
async def handle_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    """ارسال گزارش خطا به مدیر"""
    error_text = f"⚠️ خطا در ربات:\n\n{context.error}"
    print(error_text)
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=error_text)
    except:
        pass

# ======================= 🚀 اجرای نهایی سیستم =======================
if __name__ == "__main__":
    print("🤖 خنگول فارسی 8.6.2 Cloud+ Fusion Ultra AI+ آماده به خدمت است ...")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_error_handler(handle_error)

# 🔹 دستورات اصلی
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", show_custom_help))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("fullstats", fullstats))   # ← اینجا اضافه کن
    app.add_handler(CommandHandler("broadcast", broadcast))   # ← و این
    app.add_handler(CommandHandler("reset", reset_memory))
    app.add_handler(CommandHandler("reload", reload_memory))
    app.add_handler(CommandHandler("backup", backup))
    app.add_handler(CommandHandler("restore", restore))
    app.add_handler(CommandHandler("cloudsync", cloudsync))
    app.add_handler(CommandHandler("leave", leave))

    # 🔹 راهنما
    app.add_handler(MessageHandler(filters.Regex("^ثبت راهنما$"), save_custom_help))
    app.add_handler(MessageHandler(filters.Regex("^راهنما$"), show_custom_help))

    # 🔹 فایل‌ها، خوشامد و پیام‌ها
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))

    # 🔹 شروع وظایف خودکار
    async def on_startup(app):
        await notify_admin_on_startup(app)
        app.create_task(auto_backup(app.bot))
        print("🌙 [SYSTEM] Startup tasks scheduled ✅")

    app.post_init = on_startup
    app.run_polling(allowed_updates=Update.ALL_TYPES)
