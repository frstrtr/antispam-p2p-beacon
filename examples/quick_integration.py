#!/usr/bin/env python3
"""
Quick Start Antispam Bot Integration

This is a minimal example showing how to integrate any local bot
with the antispam-beacon P2P network in just a few lines of code.

Usage:
    python quick_integration.py report 123456789 "spam_content"
    python quick_integration.py check 123456789
    python quick_integration.py unban 123456789
"""

import requests
import sys
import time

# Antispam Beacon Server Configuration
BEACON_URL = "http://localhost:8081"
TIMEOUT = 5

def report_spammer(user_id: str, reason: str = "spam_detected") -> bool:
    """
    Report a spammer to the P2P network.
    
    This is the MAIN function you'll use in your bot to report detected spammers.
    The server automatically propagates this to all connected P2P peers.
    """
    try:
        response = requests.post(
            f"{BEACON_URL}/report_id",
            json={
                "user_id": str(user_id),
                "reason": reason,
                "source": "my_bot",
                "timestamp": int(time.time())
            },
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS: Spammer {user_id} reported to P2P network")
            print(f"   Reason: {reason}")
            print(f"   Response: {result}")
            return True
        else:
            print(f"❌ ERROR: HTTP {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ NETWORK ERROR: {e}")
        return False

def check_spammer(user_id: str) -> dict:
    """
    Check if a user is flagged as a spammer in the P2P network.
    
    Use this BEFORE processing messages to block known spammers immediately.
    """
    try:
        response = requests.get(
            f"{BEACON_URL}/check",
            params={"user_id": str(user_id)},
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json()
            is_spammer = result.get("is_spammer", False)
            
            if is_spammer:
                print(f"🚨 SPAMMER DETECTED: User {user_id}")
                print(f"   Sources: {', '.join([k for k, v in result.items() if isinstance(v, dict) and v])}")
            else:
                print(f"✅ CLEAN: User {user_id} is not flagged")
            
            return result
        else:
            print(f"❌ ERROR: HTTP {response.status_code} - {response.text}")
            return {}
            
    except requests.exceptions.RequestException as e:
        print(f"❌ NETWORK ERROR: {e}")
        return {}

def unban_user(user_id: str, reason: str = "false_positive") -> bool:
    """
    Remove a user from the spammer database (global unban).
    
    Use this if you determine a user was falsely flagged.
    """
    try:
        response = requests.post(
            f"{BEACON_URL}/unban",
            json={
                "spammer_id": str(user_id),
                "reason": reason,
                "source": "my_bot"
            },
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            response.json()  # Validate JSON response
            print(f"✅ SUCCESS: User {user_id} unbanned from P2P network")
            print(f"   Reason: {reason}")
            return True
        else:
            print(f"❌ ERROR: HTTP {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ NETWORK ERROR: {e}")
        return False

# ============================================================================
# INTEGRATION EXAMPLES - Copy these into your bot code
# ============================================================================

def telegram_bot_example():
    """
    Example integration for a Telegram bot using python-telegram-bot.
    
    Add this to your existing bot code:
    """
    print("""
# Add this to your Telegram bot:

from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import requests

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    message = update.message.text
    
    # 1. FIRST: Check if user is known spammer
    result = check_spammer(user_id)
    if result.get("is_spammer"):
        # Block message and ban user
        await update.message.delete()
        await context.bot.ban_chat_member(update.effective_chat.id, user_id)
        return
    
    # 2. THEN: Analyze message for spam (your detection logic here)
    if detect_spam(message):  # Your spam detection function
        # Report to P2P network and take action
        if report_spammer(user_id, "promotional_content"):
            await update.message.delete()
            await context.bot.ban_chat_member(update.effective_chat.id, user_id)

def detect_spam(message: str) -> bool:
    # Your spam detection logic here
    spam_keywords = ['crypto', 'investment', 'profit', 'click here']
    return any(keyword in message.lower() for keyword in spam_keywords)
    """)

def discord_bot_example():
    """Example integration for a Discord bot using discord.py."""
    print("""
# Add this to your Discord bot:

import discord
from discord.ext import commands
import requests

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    user_id = str(message.author.id)
    
    # 1. Check if user is known spammer
    result = check_spammer(user_id)
    if result.get("is_spammer"):
        await message.delete()
        await message.author.ban(reason="Known spammer from P2P network")
        return
    
    # 2. Analyze message content
    if detect_spam(message.content):
        if report_spammer(user_id, "spam_detected"):
            await message.delete()
            await message.author.ban(reason="Spam detected and reported to network")
    
    await bot.process_commands(message)
    """)

def generic_bot_example():
    """Example for any bot framework."""
    print("""
# Generic integration example:

def process_user_message(user_id, message_content):
    # Step 1: Check P2P network for known spammers
    spammer_check = check_spammer(str(user_id))
    
    if spammer_check.get("is_spammer"):
        # User is known spammer - block immediately
        block_user(user_id)
        return "BLOCKED_KNOWN_SPAMMER"
    
    # Step 2: Analyze message content (your spam detection logic)
    if is_spam_content(message_content):
        # Report to P2P network
        success = report_spammer(str(user_id), "spam_content_detected")
        
        if success:
            # Take local action (ban, mute, delete, etc.)
            block_user(user_id)
            return "SPAM_REPORTED_AND_BLOCKED"
        else:
            # Network reporting failed, still take local action
            block_user(user_id)
            return "SPAM_BLOCKED_LOCALLY"
    
    return "MESSAGE_ALLOWED"

def is_spam_content(message):
    # Your spam detection logic here
    # This could be ML model, rules, keyword matching, etc.
    pass

def block_user(user_id):
    # Your platform-specific user blocking code
    pass
    """)

def main():
    """Command line interface for testing."""
    if len(sys.argv) < 3:
        print("Antispam Beacon Quick Integration Tool")
        print("=" * 50)
        print("Usage:")
        print("  python quick_integration.py report <user_id> [reason]")
        print("  python quick_integration.py check <user_id>")
        print("  python quick_integration.py unban <user_id> [reason]")
        print("  python quick_integration.py examples")
        print()
        print("Examples:")
        print("  python quick_integration.py report 123456789 'promotional_spam'")
        print("  python quick_integration.py check 123456789")
        print("  python quick_integration.py unban 123456789 'false_positive'")
        print()
        print("Integration Examples:")
        print("  python quick_integration.py examples")
        sys.exit(1)
    
    action = sys.argv[1].lower()
    
    if action == "examples":
        print("🤖 BOT INTEGRATION EXAMPLES")
        print("=" * 50)
        telegram_bot_example()
        discord_bot_example()
        generic_bot_example()
        return
    
    if len(sys.argv) < 3:
        print("❌ Please provide a user_id")
        sys.exit(1)
    
    user_id = sys.argv[2]
    
    print(f"🤖 Antispam Beacon Integration - {action.upper()}")
    print("=" * 50)
    
    if action == "report":
        reason = sys.argv[3] if len(sys.argv) > 3 else "spam_detected"
        success = report_spammer(user_id, reason)
        if success:
            print("🌐 Spammer data has been propagated to all P2P network peers")
        sys.exit(0 if success else 1)
    
    elif action == "check":
        result = check_spammer(user_id)
        if result.get("is_spammer"):
            print("⚠️  RECOMMENDATION: Block this user in your application")
        else:
            print("✅ RECOMMENDATION: User appears clean, allow messages")
        sys.exit(0)
    
    elif action == "unban":
        reason = sys.argv[3] if len(sys.argv) > 3 else "false_positive"
        success = unban_user(user_id, reason)
        if success:
            print("🌐 Unban has been propagated to all P2P network peers")
        sys.exit(0 if success else 1)
    
    else:
        print(f"❌ Unknown action: {action}")
        print("Available actions: report, check, unban, examples")
        sys.exit(1)

if __name__ == "__main__":
    main()
