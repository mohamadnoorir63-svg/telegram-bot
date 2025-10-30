from telethon.sync import TelegramClient
from telethon.sessions import StringSession

print("📱 لطفاً API ID و API HASH خود را وارد کنید:")
api_id = int(input("API ID: "))
api_hash = input("API HASH: ")

with TelegramClient(StringSession(), api_id, api_hash) as client:
    print("📲 حالا شماره موبایل تلگرام خود را وارد کنید:")
    print("📞 مثال: +989123456789")
    client.start()
    session_string = client.session.save()
    print("\n✅ SESSION_STRING شما آماده است:\n")
    print(session_string)
    print("\n📋 این رشته را در تنظیمات Heroku در بخش Config Vars با کلید 'SESSION_STRING' ذخیره کنید.")
