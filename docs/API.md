# Antispam Beacon API Documentation

## Overview

The Antispam Beacon Server provides multiple API interfaces for spam detection and management:

- **HTTP REST API**: Standard HTTP endpoints for integration
- **WebSocket API**: Real-time bidirectional communication
- **P2P Protocol**: Inter-node communication protocol

## HTTP REST API

Base URL: `http://localhost:8081`

### Authentication

All APIs are restricted to localhost (127.0.0.1) for security. No additional authentication is required for local access.

### Endpoints

#### 1. Check Spam Status

Check if a user ID is flagged as a spammer.

**GET** `/check?user_id={user_id}`

**POST** `/check`
```json
{
    "user_id": "12345"
}
```

**Response:**
```json
{
    "is_spammer": true,
    "user_id": "12345",
    "timestamp": 1692123456.789,
    "reason": "spam_behavior",
    "reporter_node": "node-uuid-12345"
}
```

#### 2. Report Spammer

Report a new spammer to the network.

**POST** `/report_id`
```json
{
    "user_id": "12345",
    "reason": "spam_behavior"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Spammer reported successfully",
    "user_id": "12345"
}
```

#### 3. Global Unban (Remove Spammer)

Remove a spammer from the global database with network propagation.

**POST** `/unban`
```json
{
    "user_id": "12345"
}
```

**Response:**
```json
{
    "success": true,
    "message": "User unbanned successfully",
    "user_id": "12345",
    "found": true
}
```

#### 4. Legacy Remove ID (Deprecated)

Legacy endpoint for removing spammer IDs. Redirects to `/unban`.

**POST** `/remove_id`
```json
{
    "user_id": "12345"
}
```

## WebSocket API

Connect to: `ws://localhost:9000`

### Message Format

Send JSON messages to check spam status:

```json
{
    "user_id": "12345"
}
```

**Response:**
```json
{
    "is_spammer": false,
    "user_id": "12345"
}
```

### Example JavaScript Client

```javascript
const ws = new WebSocket('ws://localhost:9000');

ws.onopen = function() {
    console.log('Connected to Antispam Beacon');
    
    // Check a user ID
    ws.send(JSON.stringify({user_id: "12345"}));
};

ws.onmessage = function(event) {
    const response = JSON.parse(event.data);
    console.log('Spam check result:', response);
};
```

## P2P Protocol

The P2P protocol is used for inter-node communication and is not intended for direct client use.

### Message Types

- `handshake_init`: Initial peer connection
- `handshake_response`: Handshake acknowledgment
- `spam_report`: New spammer report propagation
- `gunban`: Global unban request propagation
- `data_sync`: Database synchronization (future feature)

### Security

- Messages include node UUIDs for identification
- Loop prevention through message ID tracking
- Automatic peer discovery and connection management

## Error Handling

### HTTP Status Codes

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request format
- `403 Forbidden`: Access denied (non-localhost)
- `404 Not Found`: Endpoint not found
- `500 Internal Server Error`: Server error

### Error Response Format

```json
{
    "error": true,
    "message": "Error description",
    "code": "ERROR_CODE"
}
```

## Rate Limiting

The server implements basic rate limiting to prevent abuse:

- Maximum 100 requests per minute per IP
- Burst allowance of 10 requests
- Automatic temporary blocking for excessive requests

## Integration Examples

### Python Client

```python
import requests
import json

# Check spam status
response = requests.get('http://localhost:8081/check?user_id=12345')
result = response.json()

if result.get('is_spammer'):
    print(f"User {result['user_id']} is flagged as spammer")
else:
    print(f"User {result['user_id']} is clean")

# Report spammer
data = {
    'user_id': '54321',
    'reason': 'promotional_spam'
}
response = requests.post('http://localhost:8081/report_id', json=data)
```

### cURL Examples

```bash
# Check spam status
curl "http://localhost:8081/check?user_id=12345"

# Report spammer
curl -X POST http://localhost:8081/report_id \
  -H "Content-Type: application/json" \
  -d '{"user_id":"12345","reason":"spam_behavior"}'

# Unban user
curl -X POST http://localhost:8081/unban \
  -H "Content-Type: application/json" \
  -d '{"user_id":"12345"}'
```

## Monitoring and Logging

- All API requests are logged to `server.log`
- P2P network activity is logged with color-coded output
- Database operations include audit trails
- WebSocket connections are monitored and logged

For more detailed information, see the main README.md file.
