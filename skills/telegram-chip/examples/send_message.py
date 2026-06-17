#!/usr/bin/env python3
"""
Example script for sending messages via the Telegram API.

Usage:
    python examples/send_message.py <chat_id> "Your message here"
    python examples/send_message.py @username "Your message here"

Prerequisites:
1. Start the Telegram API service: docker compose up telegram-api
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram_client import TelegramClient, TelegramClientError


def main():
    if len(sys.argv) < 3:
        print("Usage: python send_message.py <chat_id> <message>")
        print("  chat_id: Numeric ID or @username")
        print("  message: The message to send")
        print("\nExample:")
        print('  python send_message.py @username "Hello from the script!"')
        sys.exit(1)

    chat_id = sys.argv[1]
    message = sys.argv[2]

    # Try to convert to int if it looks like a number
    try:
        chat_id = int(chat_id)
    except ValueError:
        pass  # Keep as string (username)

    client = TelegramClient()

    try:
        result = client.send_message(chat_id=chat_id, message=message)
        print(f"Success: {result}")
    except TelegramClientError as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    main()
