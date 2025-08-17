# Antispam Beacon Server

A distributed peer-to-peer antispam server system that provides real-time spam detection and prevention through collaborative network intelligence.

## Overview

The Antispam Beacon Server is a P2P network node that:
- Maintains a distributed database of known spammer IDs
- Provides HTTP REST APIs for spam checking and reporting
- Propagates spam reports across the P2P network
- Offers WebSocket interface for real-time communications
- Implements unified global unban (gunban) functionality

## Features

### Core Functionality
- **Spam Detection**: Check if user IDs are known spammers
- **Spam Reporting**: Report new spammer IDs to the network
- **Global Unban**: Remove spammer records with network propagation
- **P2P Synchronization**: Automatic propagation of spam data across nodes

### Network Architecture
- **P2P Protocol**: Custom JSON-based messaging protocol
- **Bootstrap Discovery**: Automatic connection to network bootstrap nodes
- **Redundancy**: Multi-node redundancy for high availability
- **Loop Prevention**: Message deduplication to prevent network loops

### APIs
- **HTTP REST API**: Standard HTTP endpoints for integration
- **WebSocket API**: Real-time bidirectional communication
- **Local-only Security**: APIs restricted to localhost for security

## Quick Start

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd antispam-beacon
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment (optional):
```bash
cp .env.example .env
# Edit .env with your settings
```

### Running the Server

Basic startup:
```bash
python server/prime_radiant.py
```

With custom port:
```bash
python server/prime_radiant.py 9828
```

With specific peer connections:
```bash
python server/prime_radiant.py 9828 peer1.example.com:9828 peer2.example.com:9828
```

## Configuration

### Environment Variables

Create a `.env` file or set environment variables:

```env
# Bootstrap nodes for P2P network discovery
BOOTSTRAP_ADDRESSES=node1.example.com:9828,node2.example.com:9828

# Server ports (optional, defaults shown)
DEFAULT_P2P_PORT=9828
WEBSOCKET_PORT=9000
HTTP_API_PORT=8081

# Database file
DATABASE_FILE=spammers.db
```

### Network Ports

- **P2P Port**: 9828 (default) - Inter-node communication
- **HTTP API Port**: 8081 - REST API endpoints
- **WebSocket Port**: 9000 - Real-time WebSocket connections

## API Reference

### HTTP REST API

All endpoints are available at `http://localhost:8081/`

#### Check Spam Status
```http
GET /check?user_id=12345
POST /check
Content-Type: application/json
{"user_id": "12345"}
```

#### Report Spammer
```http
POST /report_id
Content-Type: application/json
{"user_id": "12345", "reason": "spam_behavior"}
```

#### Remove Spammer (Global Unban)
```http
POST /unban
Content-Type: application/json
{"user_id": "12345"}
```

#### Legacy Remove ID
```http
POST /remove_id
Content-Type: application/json
{"user_id": "12345"}
```

### WebSocket API

Connect to `ws://localhost:9000/` for real-time spam checking:

```javascript
const ws = new WebSocket('ws://localhost:9000/');
ws.send(JSON.stringify({user_id: "12345"}));
```

## Architecture

### System Components

1. **Prime Radiant** (`prime_radiant.py`)
   - Main server application entry point
   - Coordinates all subsystems
   - Handles server startup and shutdown

2. **P2P Network** (`server/p2p/`)
   - `factory.py`: Connection management and message propagation
   - `protocol.py`: P2P message handling and peer communication
   - `address.py`: Peer address management
   - `utils.py`: Network utilities

3. **Database Layer** (`server/database.py`)
   - SQLite database operations
   - Spammer data storage and retrieval
   - Database schema management

4. **API Layer** (`server/api.py`)
   - HTTP REST API endpoints
   - Request validation and processing
   - Integration with P2P network

5. **WebSocket Interface** (`server/websocket.py`)
   - Real-time WebSocket communication
   - Bidirectional message handling

### Database Schema

```sql
CREATE TABLE spammers (
    user_id TEXT PRIMARY KEY,
    timestamp REAL,
    reason TEXT,
    reporter_node TEXT,
    additional_data TEXT
);
```

### P2P Protocol

The P2P protocol uses JSON messages for communication:

#### Message Types
- `handshake_init`: Initial peer connection
- `handshake_response`: Handshake acknowledgment
- `spam_report`: New spammer report
- `gunban`: Global unban request
- `data_sync`: Database synchronization

#### Message Format
```json
{
    "type": "spam_report",
    "user_id": "12345",
    "timestamp": 1692123456.789,
    "reason": "spam_behavior",
    "reporter_node": "node-uuid",
    "message_id": "unique-message-id"
}
```

## Security Considerations

- **Localhost Only**: HTTP and WebSocket APIs are restricted to localhost
- **Input Validation**: All user inputs are validated and sanitized
- **Rate Limiting**: Built-in protection against spam reporting abuse
- **Message Authentication**: P2P messages include node identification

## Development

### Project Structure
```
antispam-beacon/
├── server/
│   ├── prime_radiant.py      # Main application
│   ├── database.py           # Database operations
│   ├── api.py               # HTTP REST API
│   ├── websocket.py         # WebSocket interface
│   ├── server_config.py     # Configuration
│   └── p2p/                 # P2P networking
│       ├── factory.py       # Connection management
│       ├── protocol.py      # Message handling
│       ├── address.py       # Peer addressing
│       └── utils.py         # Utilities
├── requirements.txt         # Dependencies
└── README.md               # This file
```

### Testing

Run the included test scripts:
```bash
python test_unban.py
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the API documentation
- Review the logs in `server.log`

## Changelog

### Current Version
- Unified gunban (global unban) functionality
- Enhanced P2P message propagation
- Improved error handling and logging
- Comprehensive API documentation
- WebSocket real-time interface
