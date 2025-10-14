import os
import json
import random
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

# ======================= ⚙️ وضعیت عمومی و تنظیمات پایه =======================
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
    """ذخیره وضعیت در فایل برای ماندگاری بعد از ری‌استارت"""
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)


def load_status():
    """بازیابی وضعیت از فایل ذخیره‌شده"""
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                status.update(saved)
        except Exception:
            pass


load_status()  # بارگذاری وضعیت در شروع


# ======================= 🤖 کنترل احساس و لحن =======================
def detect_emotion(text: str) -> str:
    """تشخیص احساس متن بر اساس کلمات ساده"""
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
    """زیباسازی پاسخ‌ها با ایموجی بر اساس احساس"""
    emotion_map = {
        "sad": ["😔", "💭", "🕊️"],
        "happy": ["😄", "🌈", "✨"],
        "angry": ["😤", "🔥", "💢"],
        "love": ["❤️", "🥰", "💞"],
        "neutral": ["🙂", "🤖"]
    }

    for key, emjs in emotion_map.items():
        if key in sentence:
            return sentence + " " + random.choice(emjs)

    if len(sentence) < 5:
        return sentence + " 🙂"
    return sentence + " " + random.choice(["🤖", "😄", "🌸", "🪄", "✨"])


# ======================= 💞 حافظه احساس کاربران =======================
emotion_memory = {}


def remember_emotion(user_id: int, emotion: str):
    """ذخیره آخرین احساس کاربر"""
    emotion_memory[user_id] = {
        "emotion": emotion,
        "time": datetime.now().isoformat()
    }


def get_last_emotion(user_id: int):
    """برگشت آخرین احساس کاربر"""
    return emotion_memory.get(user_id, {}).get("emotion", None)


def emotion_context_reply(current_emotion: str, last_emotion: str):
    """پاسخ بر اساس تغییر احساس"""
    if not last_emotion:
        return None
    if current_emotion == last_emotion:
        return None
    if last_emotion == "sad" and current_emotion == "happy":
        return "خوشحالم حالت بهتر شده 🌤️"
    if last_emotion == "happy" and current_emotion == "sad":
        return "چی شد که ناراحت شدی؟ 💭"
    if last_emotion == "angry" and current_emotion == "love":
        return "عجب تغییر مثبتی 😍"
    return None


# ======================= 🔘 کنترل روشن/خاموش شدن ربات =======================
async def toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """روشن یا خاموش کردن ربات (فقط مدیر اصلی)"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")
    status["active"] = not status["active"]
    save_status()
    msg = "✅ ربات فعال شد!" if status["active"] else "😴 ربات خاموش شد (فقط در حال یادگیری)"
    await update.message.reply_text(msg)


# ======================= 🔒 قفل و باز کردن یادگیری =======================
async def lock_learning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """قفل کردن یادگیری خودکار (فقط مدیر اصلی)"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")
    status["locked"] = True
    save_status()
    await update.message.reply_text("🔒 یادگیری خودکار قفل شد!")


async def unlock_learning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """باز کردن قفل یادگیری (فقط مدیر اصلی)"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")
    status["locked"] = False
    save_status()
    await update.message.reply_text("🔓 یادگیری خودکار باز شد!")


# ======================= 🎭 تغییر مود پاسخ‌دهی =======================
async def mode_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تغییر مود پاسخ‌دهی (شوخ، بی‌ادب، غمگین، نرمال)"""
    if not context.args:
        return await update.message.reply_text("🎭 استفاده: /mode شوخ | نرمال | بی‌ادب | غمگین")

    mood = context.args[0].lower()
    valid_modes = ["شوخ", "بی‌ادب", "غمگین", "نرمال"]
    if mood not in valid_modes:
        return await update.message.reply_text("❌ مود نامعتبر است! گزینه‌های مجاز: شوخ، بی‌ادب، غمگین، نرمال")

    status["mode"] = mood
    save_status()
    await update.message.reply_text(f"🎭 مود پاسخ‌دهی به «{mood}» تغییر کرد 😎")


# ======================= 💬 ریپلی مود =======================
async def toggle_reply_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """روشن یا خاموش کردن ریپلی مود (فقط مدیران یا مدیر اصلی)"""
    user = update.effective_user
    chat = update.effective_chat

    # فقط مدیر اصلی یا ادمین‌های گروه مجازند
    if user.id != ADMIN_ID:
        try:
            member = await context.bot.get_chat_member(chat.id, user.id)
            if member.status not in ["administrator", "creator"]:
                return await update.message.reply_text("⛔ فقط مدیران گروه می‌تونن حالت ریپلی رو تغییر بدن!")
        except:
            return await update.message.reply_text("⛔ فقط مدیران گروه می‌تونن این دستور رو اجرا کنن!")

    # تغییر وضعیت
    status["reply_mode"] = not status.get("reply_mode", False)
    save_status()
    if status["reply_mode"]:
        await update.message.reply_text("💬 حالت ریپلی *روشن شد!* 🔄\n📢 فقط در صورت ریپلای به پیام‌های من پاسخ می‌دم.")
    else:
        await update.message.reply_text("💬 حالت ریپلی *خاموش شد!* 🗣️\n🔓 دوباره با همه صحبت می‌کنم.")


async def should_reply(update: Update) -> bool:
    """تشخیص اینکه ربات باید پاسخ بده یا نه"""
    if status.get("reply_mode", False):
        if update.message.reply_to_message and update.message.reply_to_message.from_user.is_bot:
            return True
        if update.message.text and "خنگول کجایی" in update.message.text:
            return True
        return False
    return True


async def handle_reply_mode(update: Update):
    """پاسخ مخصوص وقتی ریپلی مود فعاله"""
    if update.message.text and "خنگول کجایی" in update.message.text:
        await update.message.reply_text(
            random.choice([
                "😴 همینجام قربان، داشتم به چیزای عمیق فکر می‌کردم 🤖",
                "👋 اینجام رئیس! در حالت ریپلی فقط صدام کنی جواب می‌دم 💬",
                "😌 خستم ولی هوشیارم، تو بگو!"
            ])
        )
import random
import os
import json
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime

# ======================= 🧠 یادگیری و حافظه =======================
def load_data(filename: str):
    """خواندن داده از فایل JSON"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_data(filename: str, data):
    """ذخیره داده در فایل JSON"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[ERROR] ذخیره فایل {filename}: {e}")


def learn(phrase, *responses):
    """یادگیری دستی جمله و پاسخ‌ها"""
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
    """یادگیری در حالت خاموشی (بدون پاسخ‌دهی)"""
    if not phrase.strip():
        return
    data = load_data("memory.json")
    phrases = data.get("phrases", {})
    if phrase not in phrases:
        phrases[phrase] = [response] if response else []
        save_data("memory.json", data)


def auto_learn_from_text(text):
    """یادگیری خودکار از گفت‌وگوهای عمومی"""
    if not text or len(text) < 4:
        return
    data = load_data("memory.json")
    phrases = data.get("phrases", {})
    if text not in phrases:
        phrases[text] = []
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
    """ثبت جوک جدید با ریپلای (پشتیبانی از متن، عکس، ویدیو، استیکر)"""
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
    """ثبت فال جدید با ریپلای"""
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
    """نمایش لیست همه جوک‌ها"""
    data = load_data("jokes.json")
    if not data:
        return await update.message.reply_text("📂 هیچ جوکی ثبت نشده 😅")

    msg = "\n".join([f"{k}. {v.get('value', '')[:30]}..." for k, v in data.items()])
    await update.message.reply_text("😂 لیست جوک‌ها:\n" + msg)


async def list_fortunes(update: Update):
    """نمایش لیست فال‌ها"""
    data = load_data("fortunes.json")
    if not data:
        return await update.message.reply_text("📂 هنوز هیچ فالی ثبت نشده 😔")

    msg = "\n".join([f"{k}. {v.get('value', '')[:30]}..." for k, v in data.items()])
    await update.message.reply_text("🔮 لیست فال‌ها:\n" + msg)


async def delete_joke(update: Update):
    """حذف جوک با ریپلای"""
    replied = update.message.reply_to_message
    if not replied:
        return await update.message.reply_text("❗ باید روی جوک ریپلای کنی برای حذف.")
    data = load_data("jokes.json")
    to_delete = None
    for k, v in data.items():
        if v.get("value") == replied.text:
            to_delete = k
            break
    if not to_delete:
        return await update.message.reply_text("❌ جوک پیدا نشد.")
    del data[to_delete]
    save_data("jokes.json", data)
    await update.message.reply_text("🗑️ جوک حذف شد!")


async def delete_fortune(update: Update):
    """حذف فال با ریپلای"""
    replied = update.message.reply_to_message
    if not replied:
        return await update.message.reply_text("❗ باید روی فال ریپلای کنی برای حذف.")
    data = load_data("fortunes.json")
    to_delete = None
    for k, v in data.items():
        if v.get("value") == replied.text:
            to_delete = k
            break
    if not to_delete:
        return await update.message.reply_text("❌ فال پیدا نشد.")
    del data[to_delete]
    save_data("fortunes.json", data)
    await update.message.reply_text("🗑️ فال حذف شد!")


# ======================= 🧮 محاسبه درصد هوش =======================
async def show_intelligence(update: Update):
    """محاسبه درصد هوش خنگول با جزئیات واقعی و زیبا"""
    score = 0
    details = []

    # 🧠 حافظه گفتاری
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

    # 🔮 خلاقیت و پیش‌بینی
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
            details.append("👥 اجتماعی و فعال در چندین گروه 📈")

    # ❤️ احساسات
    user_id = update.effective_user.id
    last_emotion = get_last_emotion(user_id)
    if last_emotion:
        score += 5
        details.append(f"💞 احساس اخیر: {last_emotion}")

    total = min(100, score)
    msg = (
        f"🧠 درصد هوش خنگول: {total}%\n\n" +
        "\n".join(details) +
        "\n\n🌟 وضعیت کلی: " +
        ("🚀 نابغه خلاق و اجتماعی" if total >= 80 else
         "💡 باهوش و رشد‌یابنده" if total >= 50 else
         "🐣 در مسیر یادگیری")
    )

    await update.message.reply_text(msg)


# ======================= 🪄 ساخت جمله تصادفی =======================
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
import os
import json
import shutil
import zipfile
import asyncio
import random
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

# ======================= 🧠 مدیریت فایل‌های حافظه =======================
def init_files():
    """بررسی و ایجاد فایل‌های اصلی حافظه در صورت نبود"""
    required_files = [
        "memory.json",
        "group_data.json",
        "jokes.json",
        "fortunes.json"
    ]
    for file in required_files:
        if not os.path.exists(file):
            with open(file, "w", encoding="utf-8") as f:
                f.write("{}")
    print("✅ فایل‌های حافظه بررسی و ایجاد شدند.")


# ======================= ☁️ بک‌آپ و بازیابی =======================
def _should_include_in_backup(path: str) -> bool:
    """انتخاب فایل‌هایی که باید در بک‌آپ باشند"""
    lowered = path.lower()
    skip_dirs = ["pycache", ".git", "venv", "restore_temp"]
    if any(sd in lowered for sd in skip_dirs):
        return False
    if lowered.endswith(".zip") or os.path.basename(lowered).startswith("backup_"):
        return False
    return lowered.endswith((".json", ".jpg", ".png", ".webp", ".mp3", ".ogg"))


async def cloudsync_internal(bot, reason="Manual Backup"):
    """ایجاد و ارسال فایل ZIP بک‌آپ برای مدیر اصلی"""
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"backup_{now}.zip"
    try:
        with zipfile.ZipFile(filename, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk("."):
                for file in files:
                    full_path = os.path.join(root, file)
                    if _should_include_in_backup(full_path):
                        arcname = os.path.relpath(full_path, ".")
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


async def auto_backup(bot):
    """بک‌آپ خودکار هر ۱۲ ساعت"""
    while True:
        await asyncio.sleep(43200)
        await cloudsync_internal(bot, "Auto Backup")


async def cloudsync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اجرای بک‌آپ ابری دستی"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")
    await cloudsync_internal(context.bot, "Manual Cloud Backup")


async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ایجاد فایل ZIP و ارسال در چت فعلی"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه بک‌آپ بگیره!")
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"backup_{now}.zip"
    try:
        with zipfile.ZipFile(filename, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk("."):
                for file in files:
                    full_path = os.path.join(root, file)
                    if _should_include_in_backup(full_path):
                        arcname = os.path.relpath(full_path, ".")
                        zipf.write(full_path, arcname=arcname)
        with open(filename, "rb") as f:
            await update.message.reply_document(document=f, filename=filename)
        await update.message.reply_text("✅ بک‌آپ کامل گرفته شد!")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در گرفتن بک‌آپ:\n{e}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)


async def restore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """درخواست فایل ZIP برای بازیابی بک‌آپ"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")
    await update.message.reply_text("📂 لطفاً فایل ZIP بک‌آپ را ارسال کن تا بازیابی شود.")
    context.user_data["await_restore"] = True


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت فایل ZIP و بازیابی محتوا"""
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
            zip_ref.extractall(restore_dir)

        important_files = ["memory.json", "group_data.json", "jokes.json", "fortunes.json"]
        moved_any = False

        for fname in important_files:
            src = os.path.join(restore_dir, fname)
            if os.path.exists(src):
                shutil.move(src, fname)
                moved_any = True

        init_files()

        if moved_any:
            await update.message.reply_text("✅ بازیابی کامل انجام شد!")
        else:
            await update.message.reply_text("ℹ️ هیچ فایلی برای جایگزینی پیدا نشد.")

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در بازیابی:\n{e}")
    finally:
        if os.path.exists(restore_zip):
            os.remove(restore_zip)
        if os.path.exists(restore_dir):
            shutil.rmtree(restore_dir)
        context.user_data["await_restore"] = False


# ======================= 👋 خوشامدگویی خودکار =======================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال پیام خوش‌آمد با عکس پروفایل"""
    if not status["welcome"]:
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


# ======================= 📊 آمارها =======================
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آمار خلاصه با طراحی زیبا"""
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


async def fullstats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آمار کامل گروه‌ها"""
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

        if len(text) > 3900:
            text = text[:3900] + "\n... (متن کوتاه شد)"
        await update.message.reply_html(text)

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در آمار گروه‌ها:\n{e}")


# ======================= 👑 شناسایی حضور مدیر اصلی =======================
async def detect_admin_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """وقتی مدیر اصلی (سودو) وارد گروه می‌شود"""
    user = update.effective_user
    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]:
        return

    if user and user.id == ADMIN_ID:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        greetings = [
            "😱 وای سودو اومد! همه بپا باشید 😆",
            "👑 سازنده‌ام برگشت، درود رئیس بزرگ!",
            "🔥 خدای من! رئیس شخصاً تشریف آوردن!",
            "🤖 سلام ارباب، خنگول آماده‌ست برای خدمت!",
            f"🌟 رئیس از راه رسید ({now})"
        ]
        await update.message.reply_text(random.choice(greetings))
import aiofiles
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
)

HELP_FILE = "custom_help.txt"

# ======================= 💬 پاسخ‌دهی هوشمند اصلی =======================
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پاسخ‌دهی اصلی هوش مصنوعی خنگول"""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    uid = update.effective_user.id
    chat_id = update.effective_chat.id

    # اگر نباید پاسخ دهد (مثلاً ریپلی مود روشن است)
    if not await should_reply(update):
        shadow_learn(text, "")
        return

    # اگر در حالت ریپلی هست و کسی گفت خنگول کجایی؟
    await handle_reply_mode(update)

    # یادگیری خودکار
    if not status["locked"]:
        auto_learn_from_text(text)

    # بررسی دستورات خاص
    if text.lower() == "درصد هوش":
        return await show_intelligence(update)
    if text.lower() == "جوک":
        return await list_jokes(update)
    if text.lower() == "فال":
        return await list_fortunes(update)
    if text.lower() == "لیست جوک":
        return await list_jokes(update)
    if text.lower() == "لیست فال":
        return await list_fortunes(update)
    if text.lower() == "جمله بساز":
        return await update.message.reply_text(generate_sentence())
    if text.lower() == "ثبت جوک" and update.message.reply_to_message:
        return save_joke(update)
    if text.lower() == "ثبت فال" and update.message.reply_to_message:
        return save_fortune(update)
    if text.lower() == "حذف جوک" and update.message.reply_to_message:
        return await delete_joke(update)
    if text.lower() == "حذف فال" and update.message.reply_to_message:
        return await delete_fortune(update)

    # دریافت پاسخ از حافظه
    learned_reply = get_reply(text)
    emotion = detect_emotion(text)
    last_emotion = get_last_emotion(uid)
    context_reply = emotion_context_reply(emotion, last_emotion)
    remember_emotion(uid, emotion)

    # انتخاب بهترین پاسخ
    if context_reply:
        reply_text = enhance_sentence(context_reply)
    elif learned_reply:
        reply_text = enhance_sentence(learned_reply)
    else:
        reply_text = smart_response(text, uid)

    await update.message.reply_text(reply_text)


# ======================= 📘 راهنمای قابل ویرایش =======================
async def show_custom_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش متن راهنما از فایل"""
    if not os.path.exists(HELP_FILE):
        return await update.message.reply_text(
            "ℹ️ هنوز هیچ متنی برای راهنما ثبت نشده.\n"
            "مدیر اصلی می‌تونه با ریپلای و نوشتن «ثبت راهنما» تنظیمش کنه."
        )

    async with aiofiles.open(HELP_FILE, "r", encoding="utf-8") as f:
        text = await f.read()
    await update.message.reply_text(text)


async def save_custom_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ثبت راهنمای جدید (فقط مدیر اصلی)"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")

    if not update.message.reply_to_message or not update.message.reply_to_message.text:
        return await update.message.reply_text("❗ باید روی پیام متنی ریپلای کنی!")

    text = update.message.reply_to_message.text
    async with aiofiles.open(HELP_FILE, "w", encoding="utf-8") as f:
        await f.write(text)

    await update.message.reply_text("✅ راهنما با موفقیت ذخیره شد!")


# ======================= 📨 ارسال همگانی =======================
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال پیام همگانی به تمام کاربران و گروه‌ها"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")

    msg = " ".join(context.args)
    if not msg:
        return await update.message.reply_text("❗ بعد از /broadcast پیام را بنویس.")

    users = load_data("memory.json").get("users", [])
    groups_data = load_data("group_data.json").get("groups", {})
    group_ids = []

    if isinstance(groups_data, dict):
        group_ids = list(groups_data.keys())
    elif isinstance(groups_data, list):
        group_ids = [g.get("id") for g in groups_data if "id" in g]

    sent, failed = 0, 0
    await update.message.reply_text("🚀 ارسال پیام همگانی در حال انجام است...")

    for uid in users:
        try:
            await context.bot.send_message(chat_id=uid, text=msg)
            sent += 1
        except:
            failed += 1

    for gid in group_ids:
        try:
            await context.bot.send_message(chat_id=int(gid), text=msg)
            sent += 1
        except:
            failed += 1

    await update.message.reply_text(
        f"📨 ارسال همگانی انجام شد ✅\n"
        f"👤 کاربران: {len(users)} | 👥 گروه‌ها: {len(group_ids)}\n"
        f"✅ موفق: {sent} | ⚠️ ناموفق: {failed}"
    )


# ======================= 🧹 ریست و بارگذاری مجدد حافظه =======================
async def reset_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پاک‌سازی کامل حافظه (فقط مدیر اصلی)"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")

    for f in ["memory.json", "group_data.json", "stickers.json", "jokes.json", "fortunes.json"]:
        if os.path.exists(f):
            os.remove(f)

    init_files()
    await update.message.reply_text("🧹 حافظه به‌طور کامل پاک شد!")


async def reload_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بارگذاری مجدد حافظه از فایل‌ها"""
    init_files()
    await update.message.reply_text("🔄 حافظه دوباره بارگذاری شد!")


# ======================= ✳️ استارت و اعلان فعال‌سازی =======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پیام شروع ربات"""
    await update.message.reply_text(
        "🤖 خنگول فارسی 8.6.2 Cloud+ Fusion Ultra AI+ آماده به خدمت است!\n"
        "📘 برای دیدن لیست دستورات بنویس: راهنما"
    )


async def notify_admin_on_startup(app):
    """اعلان به مدیر در هنگام راه‌اندازی"""
    try:
        await app.bot.send_message(
            chat_id=ADMIN_ID,
            text="🚀 ربات خنگول ابری با موفقیت فعال شد ✅"
        )
        print("[INFO] Startup notification sent ✅")
    except Exception as e:
        print(f"[ERROR] Admin notify failed: {e}")


# ======================= ⚙️ خطایاب =======================
async def handle_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    """ارسال خطا برای مدیر"""
    error_text = f"⚠️ خطا در ربات:\n\n{context.error}"
    print(error_text)
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=error_text)
    except:
        pass


# ======================= 🚀 اجرای نهایی =======================
if name == "main":
    print("🤖 خنگول فارسی 8.6.2 Cloud+ Fusion Ultra AI+ آماده به خدمت است ...")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_error_handler(handle_error)

    # 🔹 دستورات اصلی
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", show_custom_help))
    app.add_handler(CommandHandler("toggle", toggle))
    app.add_handler(CommandHandler("welcome", toggle_welcome))
    app.add_handler(CommandHandler("lock", lock_learning))
    app.add_handler(CommandHandler("unlock", unlock_learning))
    app.add_handler(CommandHandler("mode", mode_change))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("fullstats", fullstats))
    app.add_handler(CommandHandler("backup", backup))
    app.add_handler(CommandHandler("restore", restore))
    app.add_handler(CommandHandler("reset", reset_memory))
    app.add_handler(CommandHandler("reload", reload_memory))
    app.add_handler(CommandHandler("cloudsync", cloudsync))
    app.add_handler(CommandHandler("broadcast", broadcast))

    # 🔹 راهنمای قابل ویرایش
    app.add_handler(MessageHandler(filters.Regex("^ثبت راهنما$"), save_custom_help))
    app.add_handler(MessageHandler(filters.Regex("^راهنما$"), show_custom_help))

    # 🔹 سایر پیام‌ها
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    # 🔹 اجرای وظایف هنگام شروع
    async def on_startup(app):
        await notify_admin_on_startup(app)
        app.create_task(auto_backup(app.bot))
        print("🌙 [SYSTEM] Startup tasks scheduled ✅")

    app.post_init = on_startup
    app.run_polling(allowed_updates=Update.ALL_TYPES)
