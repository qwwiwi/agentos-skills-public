import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION_STRING = os.getenv("TELEGRAM_SESSION_STRING")

async def test():
    print("Connecting...")
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.connect()
    print("Connected!")
    
    try:
        print("Getting dialogs...")
        dialogs = await client.get_dialogs()
        print(f"Got {len(dialogs)} dialogs")
    except FloodWaitError as e:
        print(f"FloodWait: need to wait {e.seconds} seconds")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.disconnect()

asyncio.run(test())
