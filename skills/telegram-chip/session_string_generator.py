#!/usr/bin/env python3
"""
Telegram Session String Generator (async-safe).

Generates TELEGRAM_SESSION_STRING for telegram-chip using Telethon.
Works on newer Python versions where telethon.sync may fail without
an implicit event loop.
"""

import asyncio
import getpass
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.sessions import StringSession


def load_config() -> tuple[int, str]:
    load_dotenv()
    api_id_raw = os.getenv("TELEGRAM_API_ID", "").strip()
    api_hash = os.getenv("TELEGRAM_API_HASH", "").strip()

    if not api_id_raw or not api_hash:
        print("Error: TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env")
        sys.exit(1)

    try:
        api_id = int(api_id_raw)
    except ValueError:
        print("Error: TELEGRAM_API_ID must be an integer")
        sys.exit(1)

    return api_id, api_hash


async def generate_session(api_id: int, api_hash: str, phone: str) -> str:
    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.connect()

    try:
        if not await client.is_user_authorized():
            await client.send_code_request(phone)
            code = input("Enter login code from Telegram: ").strip()

            try:
                await client.sign_in(phone=phone, code=code)
            except SessionPasswordNeededError:
                password = getpass.getpass("Enter 2FA password: ")
                await client.sign_in(password=password)

        return client.session.save()
    finally:
        await client.disconnect()


def upsert_env_session(session_string: str, env_path: Path) -> None:
    if not env_path.exists():
        env_path.write_text("", encoding="utf-8")

    lines = env_path.read_text(encoding="utf-8").splitlines(keepends=True)
    updated = False

    for i, line in enumerate(lines):
        if line.startswith("TELEGRAM_SESSION_STRING="):
            lines[i] = f"TELEGRAM_SESSION_STRING={session_string}\n"
            updated = True
            break

    if not updated:
        lines.append(f"TELEGRAM_SESSION_STRING={session_string}\n")

    env_path.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    api_id, api_hash = load_config()

    print("\n----- Telegram Session String Generator -----\n")
    print("Enter phone number in international format, e.g. +<country_code><number>")
    phone = input("Phone: ").strip()
    if not phone:
        print("Error: phone number is required")
        sys.exit(1)

    try:
        session_string = asyncio.run(generate_session(api_id, api_hash, phone))
    except Exception as e:
        print(f"\nError: {e}")
        print("Failed to generate session string. Please try again.")
        sys.exit(1)

    print("\nAuthentication successful!")
    print("\n----- Your Session String -----")
    print(f"\n{session_string}\n")
    print("Add this to your .env file as:")
    print(f"TELEGRAM_SESSION_STRING={session_string}")
    print("\nIMPORTANT: Keep this string private and never share it publicly!")

    choice = input("\nUpdate local .env automatically? (y/N): ").strip().lower()
    if choice == "y":
        env_path = Path(".env")
        upsert_env_session(session_string, env_path)
        print(".env updated successfully.")


if __name__ == "__main__":
    main()
