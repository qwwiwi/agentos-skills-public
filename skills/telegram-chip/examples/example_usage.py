#!/usr/bin/env python3
"""
Example script demonstrating how to use the Telegram client library.

Prerequisites:
1. Start the Telegram API service: docker compose up telegram-api
2. Run this script: python examples/example_usage.py

The client connects to the HTTP API running in Docker on port 8080.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram_client import TelegramClient, TelegramClientError


def main():
    # Create a client instance
    client = TelegramClient(base_url="http://localhost:8080")

    try:
        # Check API health
        health = client.health_check()
        print(f"API Health: {health}")

        # Get current user info
        print("\n--- Current User ---")
        me = client.get_me()
        print(f"User: {me}")

        # List chats
        print("\n--- Recent Chats ---")
        chats = client.get_chats(page=1, page_size=5)
        print(chats)

        # List chats with more details
        print("\n--- Chats with Metadata ---")
        detailed_chats = client.list_chats(limit=5)
        for chat in detailed_chats:
            print(f"  - {chat.get('name')} (ID: {chat.get('id')}, Unread: {chat.get('unread_count', 0)})")

        # List contacts
        print("\n--- Contacts ---")
        contacts = client.list_contacts()
        for contact in contacts[:5]:  # Show first 5
            print(f"  - {contact.get('name')} ({contact.get('username', 'no username')})")

    except TelegramClientError as e:
        print(f"Telegram API Error: {e}")
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure the Telegram API is running:")
        print("  docker compose up telegram-api")
    finally:
        client.close()


if __name__ == "__main__":
    main()
