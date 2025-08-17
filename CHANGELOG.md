# Changelog

All notable changes to the Antispam Beacon Server project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-08-17

### Added
- Initial release of Antispam Beacon Server
- P2P distributed antispam network functionality
- HTTP REST API for spam checking and reporting
- WebSocket interface for real-time communication
- Unified Global Unban (gunban) system
- SQLite database for local spam data storage
- Automatic P2P network discovery and connection
- Bootstrap node support for network initialization
- Comprehensive logging and monitoring
- Message loop prevention in P2P network
- Security restrictions (localhost-only APIs)
- Configuration via environment variables
- Example client implementations
- Comprehensive test suite
- Full API documentation

### Features
- **Spam Detection**: Real-time checking of user IDs against distributed database
- **Spam Reporting**: Report new spammers with automatic network propagation
- **Global Unban**: Unified system for removing spammer records across network
- **P2P Synchronization**: Automatic data synchronization between network nodes
- **Multi-Protocol Support**: HTTP REST, WebSocket, and P2P protocols
- **High Availability**: Redundant node architecture for fault tolerance
- **Rate Limiting**: Built-in protection against API abuse
- **Audit Logging**: Comprehensive logging of all operations

### API Endpoints
- `GET /check` - Check spam status of user ID
- `POST /check` - Check spam status (POST variant)
- `POST /report_id` - Report new spammer to network
- `POST /unban` - Global unban (remove spammer record)
- `POST /remove_id` - Legacy remove endpoint (deprecated, redirects to unban)

### WebSocket Interface
- Real-time bidirectional communication
- JSON message format for spam checking
- Persistent connection support

### P2P Protocol
- Custom JSON-based messaging protocol
- Automatic peer discovery and connection
- Message types: handshake, spam_report, gunban, data_sync
- Loop prevention with message ID tracking
- Bootstrap node support

### Configuration
- Environment variable configuration
- Default port assignments (P2P: 9828, HTTP: 8081, WebSocket: 9000)
- Bootstrap address configuration
- Database file location configuration
- Logging level configuration

### Security
- Localhost-only API access
- Input validation and sanitization
- Rate limiting protection
- Secure P2P message handling
- Audit trail logging

### Documentation
- Comprehensive README with quick start guide
- Full API documentation
- Example client implementations (Python, WebSocket)
- Setup and configuration guide
- Architecture documentation

### Dependencies
- twisted>=24.7.0 - Asynchronous networking framework
- autobahn>=24.4.2 - WebSocket support
- zope.interface>=7.1.1 - Interface definitions
- pyOpenSSL>=24.2.1 - SSL/TLS support
- service_identity>=24.2.1 - Service identity verification
- python-dotenv>=1.1.1 - Environment configuration
- requests>=2.32.3 - HTTP client
- websockets>=13.1.0 - WebSocket client for testing

### Technical Details
- Python 3.8+ compatibility
- SQLite database with automatic schema creation
- Twisted reactor-based asynchronous architecture
- JSON serialization for all message formats
- UUID-based node identification
- Timestamp-based record tracking
- Graceful error handling and recovery

### Testing
- Unit test suite for API endpoints
- Integration tests for P2P communication
- Example client scripts for manual testing
- WebSocket client for real-time testing

### Future Roadmap
- Enhanced data synchronization protocols
- Advanced spam detection algorithms
- Network topology optimization
- Performance metrics and monitoring
- Web-based administration interface
- API authentication and authorization
- Distributed consensus mechanisms
