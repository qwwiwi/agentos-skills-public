#!/usr/bin/env python3
"""
Example script for searching messages in a chat.

Usage:
    python examples/search_messages.py <chat_id> "search query"

Prerequisites:
1. Start the Telegram API service: docker compose up telegram-api
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram_client import TelegramClient, TelegramClientError


def main():
    if len(sys.argv) < 3:
        print("Usage: python search_messages.py <chat_id> <query>")
        print("\nExample:")
        print('  python search_messages.py @channel_name "important"')
        sys.exit(1)

    chat_id = sys.argv[1]
    query = sys.argv[2]

    try:
        chat_id = int(chat_id)
    except ValueError:
        pass

    client = TelegramClient()

    try:
        print(f"Searching for '{query}' in chat {chat_id}...")
        results = client.search_messages(chat_id=chat_id, query=query, limit=10)

        if not results:
            print("No messages found.")
            return

        print(f"\nFound {len(results)} message(s):\n")
        for msg in results:
            print(f"[{msg.get('date')}] ID: {msg.get('id')}")
            print(f"  {msg.get('text', '(no text)')[:100]}")
            print()

    except TelegramClientError as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    main()
