import asyncio
from userbot_module.userbot_core import start_userbot

def start_userbot():
    loop = asyncio.get_event_loop()
    loop.create_task(start_userbot())
