# Local Antispam Bot Integration Guide

## Overview

The antispam-beacon server provides multiple communication interfaces for local antispam bots to feed spammer IDs into the P2P network. Here are the best solutions ranked by use case and performance characteristics.

## 🥇 **Recommended Solution: HTTP REST API**

### **Best for:** Production bots, batch processing, simple integration

The HTTP REST API is the **most robust and recommended solution** for local antispam bot integration:

**Endpoint:** `POST http://localhost:8081/report_id`

**Example:**
```bash
curl -X POST http://localhost:8081/report_id \
  -H "Content-Type: application/json" \
  -d '{"user_id": "123456789", "reason": "promotional_spam"}'
```

**Python Integration:**
```python
import requests
import json

def report_spammer(user_id, reason="detected_spam"):
    """Report a spammer to the P2P network."""
    data = {
        "user_id": str(user_id),
        "reason": reason,
        "source": "local_bot",
        "timestamp": int(time.time())
    }
    
    try:
        response = requests.post(
            "http://localhost:8081/report_id",
            json=data,
            timeout=5
        )
        return response.json()
    except requests.RequestException as e:
        print(f"Error reporting spammer: {e}")
        return None

# Usage
result = report_spammer("123456789", "promotional_content")
if result and result.get("status") == "success":
    print("✅ Spammer reported and propagated to P2P network")
```

### **Advantages:**
- ✅ **Automatic P2P propagation** - Immediately broadcasts to all connected peers
- ✅ **Database persistence** - Stores locally for fast future lookups
- ✅ **Security** - Localhost-only access protection
- ✅ **Error handling** - Proper HTTP status codes and JSON responses
- ✅ **Synchronous** - Know immediately if the operation succeeded
- ✅ **Standard protocol** - Easy integration with any language/framework
- ✅ **Batch support** - Can send multiple requests efficiently

## 🥈 **Alternative: WebSocket Interface**

### **Best for:** Real-time monitoring, continuous checking, interactive applications

**Endpoint:** `ws://localhost:9000`

**Python Integration:**
```python
import asyncio
import websockets
import json

async def report_via_websocket(user_id, reason="spam"):
    """Report spammer via WebSocket."""
    uri = "ws://localhost:9000"
    
    async with websockets.connect(uri) as websocket:
        # Send report request
        request = {
            "action": "report",
            "user_id": str(user_id),
            "reason": reason
        }
        
        await websocket.send(json.dumps(request))
        
        # Wait for confirmation
        response = await websocket.recv()
        return json.loads(response)

# Usage
result = asyncio.run(report_via_websocket("123456789", "promotional_spam"))
```

### **Advantages:**
- ✅ **Real-time bidirectional communication**
- ✅ **Persistent connection** - Lower overhead for multiple operations
- ✅ **Streaming data** - Can handle continuous feeds
- ✅ **Lower latency** - No HTTP overhead

### **Disadvantages:**
- ❌ **More complex** - Requires async/await or threading
- ❌ **Connection management** - Need to handle disconnections
- ❌ **Limited current functionality** - Primarily designed for checking, not reporting

## 🥉 **Advanced: Direct P2P Protocol Integration**

### **Best for:** High-performance bots, custom implementations

For advanced use cases, you can integrate directly with the P2P protocol:

**Example P2P Message:**
```python
import json
import socket
import time

def send_p2p_report(user_id, reason="spam"):
    """Send spammer report directly via P2P protocol."""
    message = {
        "type": "spammer_info_broadcast",
        "user_id": str(user_id),
        "is_spammer": True,
        "source_node": "local_bot",
        "timestamp": time.time(),
        "reason": reason,
        "lols_bot_data": {},
        "cas_chat_data": {},
        "p2p_data": {
            "ok": True,
            "user_id": user_id,
            "is_spammer": True,
            "source": "local_detection"
        }
    }
    
    # Connect to P2P port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(("localhost", 9828))
        sock.send(json.dumps(message).encode('utf-8'))
        sock.close()
        return True
    except Exception as e:
        print(f"P2P connection error: {e}")
        return False
```

## 📊 **Performance Comparison**

| Method | Latency | Throughput | Complexity | Reliability |
|--------|---------|------------|------------|-------------|
| HTTP REST | Medium | High | Low | Excellent |
| WebSocket | Low | Very High | Medium | Good |
| Direct P2P | Very Low | Highest | High | Variable |

## 🏗️ **Recommended Architecture**

### **For Production Antispam Bots:**

```python
class AntispamBot:
    def __init__(self):
        self.beacon_url = "http://localhost:8081"
        self.session = requests.Session()
        self.session.timeout = 5
    
    def detect_spam(self, message, user_id):
        """Your spam detection logic here."""
        # ML model, rule-based detection, etc.
        is_spam = self.analyze_message(message)
        return is_spam
    
    def handle_spam_detection(self, user_id, reason, confidence=0.8):
        """Handle detected spam."""
        if confidence > 0.8:  # High confidence threshold
            # Report to P2P network
            result = self.report_spammer(user_id, reason)
            
            if result and result.get("status") == "success":
                print(f"✅ Spammer {user_id} reported to network")
                
                # Take local action (ban, mute, etc.)
                self.take_local_action(user_id, reason)
            else:
                print(f"❌ Failed to report spammer {user_id}")
    
    def report_spammer(self, user_id, reason):
        """Report spammer to beacon server."""
        data = {
            "user_id": str(user_id),
            "reason": reason,
            "confidence": confidence,
            "source": "local_antispam_bot",
            "timestamp": int(time.time())
        }
        
        try:
            response = self.session.post(
                f"{self.beacon_url}/report_id",
                json=data
            )
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"Network error: {e}")
            return None
    
    def check_user(self, user_id):
        """Check if user is known spammer."""
        try:
            response = self.session.get(
                f"{self.beacon_url}/check?user_id={user_id}"
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("is_spammer", False)
        except Exception as e:
            print(f"Check error: {e}")
        return False
```

## 🚀 **Quick Start Example**

```python
#!/usr/bin/env python3
"""Simple bot integration example."""

import requests
import time

def main():
    # Example: Report a detected spammer
    spammer_id = "spam_user_123"
    reason = "promotional_content_detected"
    
    # Report to P2P network
    response = requests.post(
        "http://localhost:8081/report_id",
        json={
            "user_id": spammer_id,
            "reason": reason,
            "source": "my_bot_v1.0"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Success: {result}")
        print("🌐 Spammer data propagated to P2P network")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    main()
```

## 🔧 **Configuration Tips**

### **Environment Variables:**
```bash
# .env file for production
ANTISPAM_BEACON_URL=http://localhost:8081
ANTISPAM_CONFIDENCE_THRESHOLD=0.8
ANTISPAM_BATCH_SIZE=50
ANTISPAM_RETRY_ATTEMPTS=3
```

### **Error Handling:**
```python
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_robust_session():
    """Create HTTP session with retry logic."""
    session = requests.Session()
    
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session
```

## 📝 **Summary**

**Best Solution: HTTP REST API** (`POST /report_id`)

- **Simple integration** with any programming language
- **Automatic P2P propagation** to all network peers  
- **Built-in security** and error handling
- **Production-ready** with proper logging and monitoring
- **Immediate feedback** on operation success/failure

This approach provides the perfect balance of simplicity, reliability, and performance for local antispam bot integration with the P2P network.
