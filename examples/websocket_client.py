#!/usr/bin/env python3
"""
WebSocket client example for Antispam Beacon Server.

This example demonstrates real-time communication with the server via WebSocket.
"""

import asyncio
import websockets
import json
import sys

async def check_users_websocket(user_ids):
    """Check multiple user IDs using WebSocket connection."""
    uri = "ws://localhost:9000"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to Antispam Beacon WebSocket at {uri}")
            print("-" * 60)
            
            for user_id in user_ids:
                # Send check request
                request = {"user_id": user_id}
                await websocket.send(json.dumps(request))
                print(f"📤 Checking user: {user_id}")
                
                # Receive response
                response = await websocket.recv()
                data = json.loads(response)
                
                # Display result
                if data.get("is_spammer"):
                    print(f"🚨 User {user_id} is FLAGGED as spammer")
                    if "reason" in data:
                        print(f"   Reason: {data['reason']}")
                    if "timestamp" in data:
                        import time
                        print(f"   Reported: {time.ctime(data['timestamp'])}")
                else:
                    print(f"✅ User {user_id} is CLEAN")
                
                print()
                
                # Small delay between requests
                await asyncio.sleep(0.5)
                
    except websockets.exceptions.ConnectionRefused:
        print("❌ Could not connect to WebSocket server")
        print("   Make sure the Antispam Beacon server is running")
        return False
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        return False
    
    return True

async def interactive_websocket():
    """Interactive WebSocket session."""
    uri = "ws://localhost:9000"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to Antispam Beacon WebSocket at {uri}")
            print("Type user IDs to check (press Enter after each, 'quit' to exit)")
            print("-" * 60)
            
            while True:
                user_id = input("Enter user ID: ").strip()
                
                if user_id.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not user_id:
                    continue
                
                # Send check request
                request = {"user_id": user_id}
                await websocket.send(json.dumps(request))
                
                # Receive response
                response = await websocket.recv()
                data = json.loads(response)
                
                # Display result
                if data.get("is_spammer"):
                    print(f"🚨 SPAMMER: {user_id}")
                    if "reason" in data:
                        print(f"   Reason: {data['reason']}")
                else:
                    print(f"✅ CLEAN: {user_id}")
                
                print()
                
    except websockets.exceptions.ConnectionRefused:
        print("❌ Could not connect to WebSocket server")
        print("   Make sure the Antispam Beacon server is running")
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("WebSocket Client for Antispam Beacon Server")
        print()
        print("Usage:")
        print("  python websocket_client.py interactive")
        print("  python websocket_client.py check <user_id1> [user_id2] ...")
        print()
        print("Examples:")
        print("  python websocket_client.py interactive")
        print("  python websocket_client.py check 12345 67890 spam_user")
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    
    if mode == "interactive":
        asyncio.run(interactive_websocket())
    elif mode == "check":
        if len(sys.argv) < 3:
            print("❌ Please provide at least one user ID to check")
            sys.exit(1)
        
        user_ids = sys.argv[2:]
        asyncio.run(check_users_websocket(user_ids))
    else:
        print(f"❌ Unknown mode: {mode}")
        print("Available modes: interactive, check")
        sys.exit(1)

if __name__ == "__main__":
    main()
