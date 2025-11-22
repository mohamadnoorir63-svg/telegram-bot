from telethon import TelegramClient

API_ID = 123456
API_HASH = "your_api_hash"
SESSION = "userbot2"

client2 = TelegramClient(SESSION, API_ID, API_HASH)

async def start_userbot2():
    print("⚡ یوزربات دوم در حال اجراست...")
    await client2.start()
    await client2.run_until_disconnected()
