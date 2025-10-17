# ======================= ☁️ NOORI Secure QR Backup v12.2 — Self-Healing Edition =======================
import io, os, re, json, shutil, base64, zipfile, asyncio
from datetime import datetime
import qrcode
from PIL import Image, ImageDraw, ImageFont
from telegram import Update, InputFile, Bot
from telegram.ext import ContextTypes

# 📁 مسیر پوشه‌ی بک‌آپ
BACKUP_DIR = "backups"
os.makedirs(BACKUP_DIR, exist_ok=True)

# ⚙️ فایل‌های حیاتی برای بررسی و بک‌آپ
IMPORTANT_FILES = [
    "memory.json", "group_data.json", "jokes.json",
    "fortunes.json", "warnings.json", "aliases.json"
]

# 🔑 اطلاعات ادمین و توکن برای گزارش‌دهی
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
BOT_TOKEN = os.getenv("BOT_TOKEN")


# ======================= 🩺 سیستم تعمیر خودکار JSON =======================
async def fix_json(file_path):
    """تعمیر خودکار فایل JSON خراب و ارسال گزارش تلگرام"""
    if not os.path.exists(file_path):
        return False

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            json.load(f)
        print(f"✅ {file_path} سالم است.")
        return True
    except json.JSONDecodeError as e:
        print(f"🚨 خطا در {file_path}: {e}")

        # 🗂 ساخت بک‌آپ از فایل خراب
        backup_path = file_path + ".bak"
        shutil.copy(file_path, backup_path)
        print(f"💾 نسخه پشتیبان ساخته شد: {backup_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        fixed = content.strip()
        fixed = re.sub(r'^[^\{\[]+', '', fixed)
        fixed = re.sub(r'[^\}\]]+$', '', fixed)
        fixed = re.sub(r',\s*([\}\]])', r'\1', fixed)

        if not fixed.startswith("{") and not fixed.startswith("["):
            fixed = '{"data": {}, "users": []}'

        # بستن آکولاد و براکت ناقص
        if fixed.count("{") > fixed.count("}"):
            fixed += "}" * (fixed.count("{") - fixed.count("}"))
        if fixed.count("[") > fixed.count("]"):
            fixed += "]" * (fixed.count("[") - fixed.count("]"))

        try:
            data = json.loads(fixed)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            await notify_admin(file_path, True, str(e))
            print(f"✅ فایل {file_path} تعمیر شد.")
            return True
        except Exception as e2:
            await notify_admin(file_path, False, str(e2))
            print(f"❌ خطا در تعمیر {file_path}: {e2}")
            return False


async def notify_admin(file_name, success=True, details=""):
    """ارسال گزارش تعمیر به ادمین تلگرام"""
    if not BOT_TOKEN or ADMIN_ID == 0:
        return
    try:
        bot = Bot(token=BOT_TOKEN)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "✅ تعمیر موفق" if success else "❌ خطا در تعمیر"
        msg = (
            f"🧩 گزارش سیستم تعمیر:\n\n"
            f"📁 فایل: {file_name}\n"
            f"📅 زمان: {now}\n"
            f"🔧 وضعیت: {status}\n"
            f"📝 جزئیات: {details}"
        )
        await bot.send_message(chat_id=ADMIN_ID, text=msg)
    except Exception as e:
        print(f"⚠️ ارسال گزارش به ادمین ممکن نشد: {e}")


# ======================= 💎 تعمیر خودکار پیش از بک‌آپ =======================
async def check_and_fix_all():
    """بررسی و تعمیر همه فایل‌های مهم قبل از بک‌آپ"""
    print("🔍 بررسی سلامت فایل‌ها قبل از بک‌آپ...")
    repaired = 0
    for f in IMPORTANT_FILES:
        if os.path.exists(f):
            result = await fix_json(f)
            if result:
                repaired += 1
        else:
            print(f"⚠️ فایل {f} یافت نشد.")
    print(f"🩺 بررسی کامل شد ({repaired} فایل بررسی شد).")


# ======================= 🧩 ساخت فایل ZIP بک‌آپ =======================
def create_zip_backup():
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"backup_{now}.zip"
    zip_path = os.path.join(BACKUP_DIR, filename)

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk("."):
            for file in files:
                full_path = os.path.join(root, file)
                if _should_include_in_backup(full_path):
                    arcname = os.path.relpath(full_path, ".")
                    zipf.write(full_path, arcname=arcname)
    return zip_path, now


def _should_include_in_backup(path: str) -> bool:
    skip_dirs = ["__pycache__", ".git", "venv", "restore_temp", "backups"]
    lowered = path.lower()
    if any(sd in lowered for sd in skip_dirs):
        return False
    if lowered.endswith(".zip"):
        return False
    return lowered.endswith((".json", ".jpg", ".png", ".webp", ".mp3", ".ogg"))


# ======================= 🧠 QR کد بک‌آپ =======================
def generate_qr_image(text, timestamp):
    safe_text = text[:800]
    qr = qrcode.QRCode(version=5, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=2)
    qr.add_data(safe_text)
    qr.make(fit=False)
    qr_img = qr.make_image(fill_color="#0044cc", back_color="white").convert("RGB")

    shield = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
    draw = ImageDraw.Draw(shield)
    draw.ellipse((0, 0, 120, 120), fill="#0044cc")
    draw.polygon([(60, 25), (95, 50), (85, 95), (35, 95), (25, 50)], fill="white")

    qr_w, qr_h = qr_img.size
    shield = shield.resize((qr_w // 4, qr_h // 4))
    qr_img.paste(shield, ((qr_w - shield.size[0]) // 2, (qr_h - shield.size[1]) // 2), mask=shield)

    canvas = Image.new("RGB", (qr_w, qr_h + 80), "white")
    canvas.paste(qr_img, (0, 0))
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    label = f"Backup — {timestamp}"
    w, h = draw.textsize(label, font=font)
    draw.text(((qr_w - w) // 2, qr_h + 25), label, fill="#0044cc", font=font)

    output = io.BytesIO()
    canvas.save(output, format="PNG")
    output.seek(0)
    return output


# ======================= ☁️ بک‌آپ دستی =======================
async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")

    await check_and_fix_all()  # 🧩 بررسی و تعمیر قبل از بک‌آپ

    zip_path, timestamp = create_zip_backup()
    with open(zip_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")[:800]
    qr_img = generate_qr_image(encoded, timestamp)

    await update.message.reply_photo(photo=qr_img, caption=f"☁️ بک‌آپ ساخته شد ✅\n🕓 {timestamp}")
    await update.message.reply_document(InputFile(zip_path))
    os.remove(zip_path)


# ======================= ☁️ بک‌آپ ابری خودکار =======================
async def cloudsync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")

    await check_and_fix_all()

    zip_path, timestamp = create_zip_backup()
    with open(zip_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")[:800]
    qr_img = generate_qr_image(encoded, timestamp)

    await context.bot.send_photo(chat_id=ADMIN_ID, photo=qr_img, caption=f"☁️ Cloud Backup — {timestamp}")
    await context.bot.send_document(chat_id=ADMIN_ID, document=InputFile(zip_path))
    os.remove(zip_path)


# ======================= ♻️ بازیابی ZIP با نوار درصد =======================
async def restore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")

    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        return await update.message.reply_text("📎 فایل ZIP بک‌آپ را ریپلای کن و بعد /restore بزن.")

    file = await update.message.reply_to_message.document.get_file()
    path = os.path.join(BACKUP_DIR, "restore_temp.zip")
    await file.download_to_drive(path)

    msg = await update.message.reply_text("♻️ شروع بازیابی...\n0% [▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒]")
    restore_dir = "restore_temp"
    if os.path.exists(restore_dir):
        shutil.rmtree(restore_dir)
    os.makedirs(restore_dir, exist_ok=True)

    with zipfile.ZipFile(path, "r") as zip_ref:
        files = zip_ref.namelist()
        total = len(files)
        for i, file in enumerate(files):
            zip_ref.extract(file, restore_dir)
            percent = int((i + 1) / total * 100)
            bars = int(percent / 5)
            bar = "█" * bars + "▒" * (20 - bars)
            await msg.edit_text(f"♻️ بازیابی {percent}% [{bar}]")
            await asyncio.sleep(0.1)

    moved = 0
    for f in IMPORTANT_FILES:
        src = os.path.join(restore_dir, f)
        if os.path.exists(src):
            shutil.move(src, f)
            moved += 1

    shutil.rmtree(restore_dir)
    os.remove(path)
    await msg.edit_text(f"✅ بازیابی کامل شد!\n📦 {moved} فایل بازگردانی گردید.\n🤖 سیستم آماده است.")


# ======================= 🔁 بک‌آپ خودکار هر ۶ ساعت =======================
async def auto_backup(bot):
    while True:
        try:
            await check_and_fix_all()
            zip_path, timestamp = create_zip_backup()
            with open(zip_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")[:800]
            qr_img = generate_qr_image(encoded, timestamp)
            await bot.send_photo(chat_id=ADMIN_ID, photo=qr_img, caption=f"🤖 Auto Backup — {timestamp}")
            await bot.send_document(chat_id=ADMIN_ID, document=InputFile(zip_path))
            os.remove(zip_path)
            print(f"[AUTO BACKUP] {timestamp} ✅")
        except Exception as e:
            print(f"[AUTO BACKUP ERROR] {e}")
        await asyncio.sleep(21600)
