# Beacon Mode Configuration

## Overview

**Beacon Mode Only** is a lightweight configuration that simplifies the antispam-beacon server to focus purely on P2P network communication and local spammer management.

## What Beacon Mode Does

### ✅ **Enabled Features:**
- 🔄 **P2P Network Communication** - Connects to other beacon nodes
- 📥 **Local Spammer Reporting** - Accepts reports from local antispam bots via HTTP API
- 💾 **Local Database Storage** - Stores spammer data in SQLite database
- 📡 **P2P Broadcasting** - Propagates local spammer reports to network peers
- 📨 **P2P Data Reception** - Receives spammer data from other network nodes
- 🔍 **Local Spammer Checking** - Checks database and P2P network for known spammers

### ❌ **Disabled Features:**
- 🌐 **External API Calls** - No calls to lols.bot, cas.chat, or other external services
- 🔌 **WebSocket Server** - WebSocket real-time monitoring disabled
- ⏱️ **API Timeouts** - No waiting for external API responses
- 🧠 **External Validation** - Only uses local and P2P network data

## Configuration

### **Enable Beacon Mode:**

**Option 1: Environment Variable**
```bash
export BEACON_MODE_ONLY=true
```

**Option 2: .env File**
```dotenv
BEACON_MODE_ONLY=true
```

**Option 3: Direct Configuration**
```python
# In server_config.py
BEACON_MODE_ONLY = True
```

## Use Cases

### **1. Lightweight P2P Nodes**
Perfect for resource-constrained environments where you want to participate in the P2P network without external dependencies.

### **2. Privacy-Focused Deployments**
When you don't want to make external API calls for privacy or security reasons.

### **3. High-Performance Scenarios**
Reduces latency by eliminating external API calls and WebSocket overhead.

### **4. Dedicated Relay Nodes**
Create pure P2P relay nodes that just propagate spammer information across the network.

## API Behavior in Beacon Mode

### **Endpoint Changes:**

| Endpoint | Full Mode | Beacon Mode |
|----------|-----------|-------------|
| `GET /check` | Database + P2P + External APIs | Database + P2P only |
| `POST /report_id` | ✅ Full functionality | ✅ Full functionality |
| `POST /unban` | ✅ Full functionality | ✅ Full functionality |
| `POST /remove_id` | ✅ Full functionality | ✅ Full functionality |
| WebSocket | ✅ Real-time monitoring | ❌ Disabled |

### **Response Format Changes:**

**Full Mode Response:**
```json
{
  "ok": true,
  "user_id": "123456789",
  "is_spammer": false,
  "lols_bot": {"banned": false, "reason": null},
  "cas_chat": {"ok": true, "result": {"offenses": 0}},
  "p2p": {"ok": true, "user_id": "123456789", "is_spammer": false}
}
```

**Beacon Mode Response:**
```json
{
  "ok": true,
  "user_id": "123456789", 
  "is_spammer": false,
  "lols_bot": {},
  "cas_chat": {},
  "p2p": {"ok": true, "user_id": "123456789", "is_spammer": false}
}
```

## Performance Benefits

### **Faster Response Times:**
- ⚡ **No External API Delays** - Eliminates 1-5 second external API timeouts
- 🚀 **Reduced Latency** - Database + P2P only (typically < 100ms)
- 📈 **Higher Throughput** - Can handle more requests per second

### **Lower Resource Usage:**
- 💾 **Reduced Memory** - No WebSocket connections or external API clients
- 🔌 **Fewer Network Connections** - Only P2P and local HTTP
- ⚡ **Lower CPU Usage** - Simpler request processing

## Integration Example

```python
# Your local antispam bot integration remains the same
import requests

def check_spammer_beacon_mode(user_id):
    """Check spammer in beacon mode - only local + P2P data."""
    response = requests.get(f"http://localhost:8081/check?user_id={user_id}")
    if response.status_code == 200:
        data = response.json()
        # In beacon mode, only p2p section contains meaningful data
        return data.get("is_spammer", False)
    return False

def report_spammer_beacon_mode(user_id, reason):
    """Report spammer in beacon mode - works exactly the same."""
    response = requests.post(
        "http://localhost:8081/report_id",
        json={"user_id": user_id, "reason": reason}
    )
    return response.status_code == 200

# Usage - no changes needed!
if check_spammer_beacon_mode("123456789"):
    print("🚨 Known spammer from P2P network")
else:
    print("✅ Unknown user")

report_spammer_beacon_mode("999888777", "promotional_spam")
print("📡 Reported to P2P network")
```

## Starting Beacon Mode

```bash
# Set environment variable
export BEACON_MODE_ONLY=true

# Start server
python run_server.py

# You'll see this in the logs:
# BEACON MODE ONLY: External APIs and WebSocket disabled
# WebSocket server disabled in beacon mode
# HTTP server listening on port 8081
# P2P server listening on port 9828
```

## Testing Beacon Mode

```bash
# Test with the quick integration script
python examples/quick_integration.py check 123456789

# In beacon mode, you'll see faster responses with only local/P2P data
# External API sections will be empty: "lols_bot": {}, "cas_chat": {}
```

## Network Compatibility

✅ **Fully Compatible** - Beacon mode nodes can communicate with full mode nodes  
✅ **Protocol Unchanged** - Same P2P protocol for spammer data exchange  
✅ **Mixed Networks** - Can have both beacon and full nodes in same network  
✅ **Seamless Integration** - Existing bots work without modification  

## When to Use Beacon Mode

### **Use Beacon Mode When:**
- 🏃 **Speed is critical** - Need fastest possible response times
- 🔒 **Privacy matters** - Don't want external API calls
- 💻 **Resource constraints** - Limited CPU/memory/bandwidth
- 🌐 **Network restrictions** - Can't access external APIs
- 🎯 **Dedicated relay** - Just want to relay P2P data

### **Use Full Mode When:**
- 🔍 **Comprehensive checking** - Want all available spam databases
- 📊 **Maximum accuracy** - Need external validation
- 🔌 **WebSocket needed** - Real-time monitoring required
- 🌟 **Complete features** - Want all capabilities enabled
