#!/usr/bin/env python3
"""
Simple Python client example for Antispam Beacon Server.

This example demonstrates how to interact with the server using HTTP requests.
"""

import requests
import json
import sys
import time

BASE_URL = "http://localhost:8081"

def check_spammer(user_id):
    """Check if a user ID is flagged as a spammer."""
    try:
        response = requests.get(f"{BASE_URL}/check?user_id={user_id}")
        return response.json()
    except requests.RequestException as e:
        print(f"Error checking user {user_id}: {e}")
        return None

def report_spammer(user_id, reason="spam_behavior"):
    """Report a user ID as a spammer."""
    data = {
        "user_id": user_id,
        "reason": reason
    }
    try:
        response = requests.post(f"{BASE_URL}/report_id", json=data)
        return response.json()
    except requests.RequestException as e:
        print(f"Error reporting user {user_id}: {e}")
        return None

def unban_user(user_id):
    """Remove a user from the spammer database."""
    data = {
        "user_id": user_id
    }
    try:
        response = requests.post(f"{BASE_URL}/unban", json=data)
        return response.json()
    except requests.RequestException as e:
        print(f"Error unbanning user {user_id}: {e}")
        return None

def main():
    """Main function demonstrating API usage."""
    if len(sys.argv) < 3:
        print("Usage: python simple_client.py <action> <user_id> [reason]")
        print("Actions: check, report, unban")
        print("Example: python simple_client.py check 12345")
        print("Example: python simple_client.py report 12345 'promotional spam'")
        print("Example: python simple_client.py unban 12345")
        sys.exit(1)
    
    action = sys.argv[1].lower()
    user_id = sys.argv[2]
    reason = sys.argv[3] if len(sys.argv) > 3 else "spam_behavior"
    
    print(f"Antispam Beacon Client - {action.upper()} operation for user {user_id}")
    print("-" * 60)
    
    if action == "check":
        result = check_spammer(user_id)
        if result:
            if result.get("is_spammer"):
                print(f"🚨 User {user_id} is FLAGGED as spammer")
                print(f"   Reason: {result.get('reason', 'Unknown')}")
                print(f"   Reported: {time.ctime(result.get('timestamp', 0))}")
                print(f"   Reporter: {result.get('reporter_node', 'Unknown')}")
            else:
                print(f"✅ User {user_id} is CLEAN")
        
    elif action == "report":
        result = report_spammer(user_id, reason)
        if result and result.get("success"):
            print(f"✅ User {user_id} reported successfully")
            print(f"   Reason: {reason}")
        else:
            print(f"❌ Failed to report user {user_id}")
            if result:
                print(f"   Error: {result.get('message', 'Unknown error')}")
    
    elif action == "unban":
        result = unban_user(user_id)
        if result and result.get("success"):
            if result.get("found"):
                print(f"✅ User {user_id} unbanned successfully")
            else:
                print(f"ℹ️  User {user_id} was not in spammer database")
        else:
            print(f"❌ Failed to unban user {user_id}")
            if result:
                print(f"   Error: {result.get('message', 'Unknown error')}")
    
    else:
        print(f"❌ Unknown action: {action}")
        print("Available actions: check, report, unban")

if __name__ == "__main__":
    main()
