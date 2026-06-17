import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION_STRING = os.getenv("TELEGRAM_SESSION_STRING")

async def test():
    print("Connecting...")
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.connect()
    print("Connected!")
    
    print("Getting dialogs...")
    dialogs = await asyncio.wait_for(client.get_dialogs(), timeout=10)
    print(f"Got {len(dialogs)} dialogs")
    
    await client.disconnect()
    print("Done!")

asyncio.run(test())
