"""Security utilities and logging for P2P network protection."""

# SPDX-License-Identifier: MIT
# -*- coding: utf-8 -*-
# server/p2p/security.py

import hashlib
import hmac
import json
import time
import uuid
import os
from collections import defaultdict, deque
from typing import Dict, Set, Optional, Tuple, Any
import logging
from pathlib import Path

from server.server_config import (
    NETWORK_SECRET_KEY,
    ENABLE_P2P_SECURITY,
    MAX_CONNECTIONS_PER_IP,
    CONNECTION_RATE_LIMIT,
    MESSAGE_RATE_LIMIT,
    REQUIRE_NODE_AUTHENTICATION,
    ALLOWED_NODE_KEYS,
    BLOCKED_NODE_KEYS,
    BLOCKED_IP_ADDRESSES,
    ENABLE_MESSAGE_SIGNING,
    REJECT_UNSIGNED_MESSAGES,
    SECURITY_LOG_FILE,
    LOG_SECURITY_EVENTS,
    LOGGER as MAIN_LOGGER
)

# Security-specific logger
SECURITY_LOGGER = logging.getLogger("security")
SECURITY_LOGGER.setLevel(logging.INFO)

# Add file handler for security logs
if LOG_SECURITY_EVENTS:
    security_handler = logging.FileHandler(SECURITY_LOG_FILE)
    security_formatter = logging.Formatter(
        "%(asctime)s - SECURITY - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    security_handler.setFormatter(security_formatter)
    SECURITY_LOGGER.addHandler(security_handler)

# Add console handler for critical security events
console_handler = logging.StreamHandler()
console_formatter = logging.Formatter(
    "\033[91m[SECURITY]\033[0m %(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
console_handler.setFormatter(console_formatter)
console_handler.setLevel(logging.WARNING)
SECURITY_LOGGER.addHandler(console_handler)


class SecurityManager:
    """Manages P2P network security including authentication, rate limiting, and access control."""
    
    def __init__(self):
        """Initialize SecurityManager with configuration and security tracking."""
        self.config_file = ".env"
        self.config_mtime = 0  # Track last modification time
        self._init_security_state()
        self._load_configuration()
        self._setup_logging()
        
    def _init_security_state(self):
        """Initialize all security tracking variables."""
        # Rate limiting tracking
        self.ip_connections: Dict[str, int] = defaultdict(int)
        self.connection_attempts: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.message_rates: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Security state
        self.blocked_peers: Set[str] = set()
        self.failed_attempts: Dict[str, int] = defaultdict(int)
        self.authenticated_nodes: Dict[str, dict] = {}
        
        # Session tracking
        self.active_sessions: Dict[str, dict] = {}
        self.security_events: deque = deque(maxlen=1000)
        
    def _load_configuration(self):
        """Load security configuration from environment and track file changes."""
        current_mtime = self._get_config_mtime()
        
        # Load configuration from server_config (which reads from .env)
        self.enabled = ENABLE_P2P_SECURITY
        self.secret_key = NETWORK_SECRET_KEY
        self.max_connections_per_ip = MAX_CONNECTIONS_PER_IP
        self.connection_rate_limit = CONNECTION_RATE_LIMIT
        self.message_rate_limit = MESSAGE_RATE_LIMIT
        self.require_authentication = REQUIRE_NODE_AUTHENTICATION
        self.allowed_node_keys = set(ALLOWED_NODE_KEYS)
        self.blocked_node_keys = set(BLOCKED_NODE_KEYS)
        self.blocked_ips = set(BLOCKED_IP_ADDRESSES)
        self.enable_message_signing = ENABLE_MESSAGE_SIGNING
        self.reject_unsigned = REJECT_UNSIGNED_MESSAGES
        self.log_events = LOG_SECURITY_EVENTS
        
        self.config_mtime = current_mtime
        
        if hasattr(self, 'logger'):
            self.logger.info(f"Configuration loaded/reloaded - Enabled: {self.enabled}, "
                           f"Allowed nodes: {len(self.allowed_node_keys)}, "
                           f"Blocked nodes: {len(self.blocked_node_keys)}")
    
    def _get_config_mtime(self) -> float:
        """Get the modification time of the configuration file."""
        try:
            return os.path.getmtime(self.config_file)
        except OSError:
            return 0
    
    def check_config_reload(self):
        """Check if configuration file has changed and reload if needed."""
        current_mtime = self._get_config_mtime()
        if current_mtime > self.config_mtime:
            self.logger.info("Configuration file changed, reloading security settings...")
            
            # Reload server_config module to get fresh values
            import importlib
            import server.server_config
            importlib.reload(server.server_config)
            
            # Re-import the values
            from server.server_config import (
                NETWORK_SECRET_KEY,
                ENABLE_P2P_SECURITY,
                MAX_CONNECTIONS_PER_IP,
                CONNECTION_RATE_LIMIT,
                MESSAGE_RATE_LIMIT,
                REQUIRE_NODE_AUTHENTICATION,
                ALLOWED_NODE_KEYS,
                BLOCKED_NODE_KEYS,
                BLOCKED_IP_ADDRESSES,
                ENABLE_MESSAGE_SIGNING,
                REJECT_UNSIGNED_MESSAGES,
                SECURITY_LOG_FILE,
                LOG_SECURITY_EVENTS
            )
            
            # Update configuration
            old_allowed = self.allowed_node_keys.copy()
            old_blocked = self.blocked_node_keys.copy()
            
            self._load_configuration()
            
            # Log changes
            added_allowed = self.allowed_node_keys - old_allowed
            removed_allowed = old_allowed - self.allowed_node_keys
            added_blocked = self.blocked_node_keys - old_blocked
            removed_blocked = old_blocked - self.blocked_node_keys
            
            if added_allowed:
                self.logger.info(f"Added to whitelist: {', '.join(added_allowed)}")
            if removed_allowed:
                self.logger.info(f"Removed from whitelist: {', '.join(removed_allowed)}")
            if added_blocked:
                self.logger.warning(f"Added to blacklist: {', '.join(added_blocked)}")
            if removed_blocked:
                self.logger.info(f"Removed from blacklist: {', '.join(removed_blocked)}")
                
            self._log_security_event("config_reload", {
                "added_allowed": list(added_allowed),
                "removed_allowed": list(removed_allowed), 
                "added_blocked": list(added_blocked),
                "removed_blocked": list(removed_blocked)
            })
    
    def _log_security_event(self, event_type: str, details: dict):
        """Log a security event."""
        if self.log_events:
            timestamp = time.time()
            event = {
                "timestamp": timestamp,
                "event_type": event_type,
                "details": details
            }
            self.security_events.append(event)
            self.logger.info(f"Security event: {event_type} - {details}")
    
    def reload_configuration(self):
        """Manually trigger configuration reload."""
        self.logger.info("Manual configuration reload requested")
        self.config_mtime = 0  # Force reload
        self.check_config_reload()
        
    def _setup_logging(self):
        """Setup security logging."""
        # Create security logger
        self.logger = logging.getLogger("security")
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            # Create file handler for security events
            log_file = SECURITY_LOG_FILE if hasattr(MAIN_LOGGER, 'handlers') else "security.log"
            handler = logging.FileHandler(log_file)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            
        self.logger.info("SecurityManager initialized")

    def is_connection_allowed(self, ip_address: str, node_uuid: str = None) -> Tuple[bool, str]:
        """
        Check if a connection is allowed based on security policies.
        
        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        if not self.security_enabled:
            return True, "Security disabled"
            
        # Check IP blacklist
        if ip_address in self.blocked_ips:
            SECURITY_LOGGER.warning(f"Connection blocked: IP {ip_address} is blacklisted")
            return False, "IP address blocked"
            
        # Check node blacklist
        if node_uuid and node_uuid in self.blocked_nodes:
            SECURITY_LOGGER.warning(f"Connection blocked: Node {node_uuid} is blacklisted")
            return False, "Node UUID blocked"
            
        # Check node whitelist (if configured)
        if self.allowed_nodes and node_uuid and node_uuid not in self.allowed_nodes:
            SECURITY_LOGGER.warning(f"Connection blocked: Node {node_uuid} not in whitelist")
            return False, "Node UUID not in whitelist"
            
        # Check connection limit per IP
        if self.connection_counts[ip_address] >= MAX_CONNECTIONS_PER_IP:
            SECURITY_LOGGER.warning(f"Connection blocked: IP {ip_address} exceeded connection limit ({MAX_CONNECTIONS_PER_IP})")
            return False, "Too many connections from IP"
            
        # Check connection rate limit
        current_time = time.time()
        self._cleanup_old_timestamps(self.connection_times[ip_address], current_time, 60)
        
        if len(self.connection_times[ip_address]) >= CONNECTION_RATE_LIMIT:
            SECURITY_LOGGER.warning(f"Connection blocked: IP {ip_address} exceeded rate limit ({CONNECTION_RATE_LIMIT}/min)")
            return False, "Connection rate limit exceeded"
            
        return True, "Connection allowed"
        
    def register_connection(self, ip_address: str, node_uuid: str = None):
        """Register a new connection for tracking."""
        if not self.security_enabled:
            return
            
        self.connection_counts[ip_address] += 1
        self.connection_times[ip_address].append(time.time())
        
        SECURITY_LOGGER.info(f"Connection registered: IP {ip_address}, Node {node_uuid}")
        
    def unregister_connection(self, ip_address: str, node_uuid: str = None):
        """Unregister a connection when it's closed."""
        if not self.security_enabled:
            return
            
        if self.connection_counts[ip_address] > 0:
            self.connection_counts[ip_address] -= 1
            
        if node_uuid in self.authenticated_nodes:
            self.authenticated_nodes.discard(node_uuid)
            
        SECURITY_LOGGER.info(f"Connection unregistered: IP {ip_address}, Node {node_uuid}")
        
    def is_message_allowed(self, ip_address: str, node_uuid: str, message_type: str) -> Tuple[bool, str]:
        """
        Check if a message is allowed based on rate limiting and authentication.
        
        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        if not self.security_enabled:
            return True, "Security disabled"
            
        # Check if node is authenticated (for non-handshake messages)
        if REQUIRE_NODE_AUTHENTICATION and message_type not in ["handshake_init", "handshake_response"]:
            if node_uuid not in self.authenticated_nodes:
                SECURITY_LOGGER.warning(f"Message blocked: Node {node_uuid} not authenticated for message type {message_type}")
                return False, "Node not authenticated"
                
        # Check message rate limit
        current_time = time.time()
        self._cleanup_old_timestamps(self.message_counts[ip_address], current_time, 60)
        
        if len(self.message_counts[ip_address]) >= MESSAGE_RATE_LIMIT:
            SECURITY_LOGGER.warning(f"Message blocked: IP {ip_address} exceeded message rate limit ({MESSAGE_RATE_LIMIT}/min)")
            return False, "Message rate limit exceeded"
            
        # Register the message
        self.message_counts[ip_address].append(current_time)
        return True, "Message allowed"
        
    def authenticate_node(self, node_uuid: str, auth_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Authenticate a node using the provided authentication data.
        
        Returns:
            Tuple of (authenticated: bool, reason: str)
        """
        if not self.security_enabled or not REQUIRE_NODE_AUTHENTICATION:
            return True, "Authentication not required"
            
        if not NETWORK_SECRET_KEY:
            SECURITY_LOGGER.error("Authentication required but no network secret key configured")
            return False, "Server configuration error"
            
        try:
            # Extract authentication components
            auth_token = auth_data.get("auth_token")
            timestamp = auth_data.get("timestamp")
            challenge = auth_data.get("challenge", node_uuid)
            
            if not auth_token or not timestamp:
                return False, "Missing authentication data"
                
            # Check timestamp to prevent replay attacks (allow 5 minute window)
            current_time = time.time()
            if abs(current_time - timestamp) > 300:  # 5 minutes
                return False, "Authentication timestamp expired"
                
            # Verify HMAC signature
            expected_token = self._generate_auth_token(node_uuid, timestamp, challenge)
            if not hmac.compare_digest(auth_token, expected_token):
                SECURITY_LOGGER.warning(f"Authentication failed: Invalid token for node {node_uuid}")
                return False, "Invalid authentication token"
                
            # Authentication successful
            self.authenticated_nodes.add(node_uuid)
            SECURITY_LOGGER.info(f"Node authenticated successfully: {node_uuid}")
            return True, "Authentication successful"
            
        except Exception as e:
            SECURITY_LOGGER.error(f"Authentication error for node {node_uuid}: {e}")
            return False, "Authentication error"
            
    def generate_auth_challenge(self, node_uuid: str) -> Dict[str, Any]:
        """Generate authentication challenge for a node."""
        if not self.security_enabled or not REQUIRE_NODE_AUTHENTICATION:
            return {}
            
        timestamp = time.time()
        challenge = str(uuid.uuid4())
        auth_token = self._generate_auth_token(node_uuid, timestamp, challenge)
        
        return {
            "auth_token": auth_token,
            "timestamp": timestamp,
            "challenge": challenge
        }
        
    def _generate_auth_token(self, node_uuid: str, timestamp: float, challenge: str) -> str:
        """Generate HMAC authentication token."""
        if not NETWORK_SECRET_KEY:
            return ""
            
        message = f"{node_uuid}:{timestamp}:{challenge}"
        return hmac.new(
            NETWORK_SECRET_KEY.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
    def verify_message_signature(self, message: Dict[str, Any], node_uuid: str) -> bool:
        """Verify message signature if message signing is enabled."""
        if not ENABLE_MESSAGE_SIGNING:
            return True
            
        if REJECT_UNSIGNED_MESSAGES and "signature" not in message:
            SECURITY_LOGGER.warning(f"Unsigned message rejected from node {node_uuid}")
            return False
            
        # For now, basic implementation - can be enhanced with actual cryptographic signatures
        signature = message.get("signature")
        if signature:
            # Remove signature for verification
            message_copy = message.copy()
            del message_copy["signature"]
            expected_signature = self._generate_message_signature(message_copy, node_uuid)
            return hmac.compare_digest(signature, expected_signature)
            
        return not REJECT_UNSIGNED_MESSAGES
        
    def _generate_message_signature(self, message: Dict[str, Any], node_uuid: str) -> str:
        """Generate message signature."""
        if not NETWORK_SECRET_KEY:
            return ""
            
        message_str = json.dumps(message, sort_keys=True)
        message_data = f"{node_uuid}:{message_str}"
        return hmac.new(
            NETWORK_SECRET_KEY.encode(),
            message_data.encode(),
            hashlib.sha256
        ).hexdigest()
        
    def sign_message(self, message: Dict[str, Any], node_uuid: str) -> Dict[str, Any]:
        """Sign a message if message signing is enabled."""
        if not ENABLE_MESSAGE_SIGNING:
            return message
            
        message_copy = message.copy()
        signature = self._generate_message_signature(message_copy, node_uuid)
        message_copy["signature"] = signature
        return message_copy
        
    def _cleanup_old_timestamps(self, timestamp_queue: deque, current_time: float, window_seconds: int):
        """Remove timestamps older than the specified window."""
        while timestamp_queue and current_time - timestamp_queue[0] > window_seconds:
            timestamp_queue.popleft()
            
    def add_blocked_node(self, node_uuid: str, reason: str = "Manual block"):
        """Add a node to the blocklist."""
        self.blocked_nodes.add(node_uuid)
        self.authenticated_nodes.discard(node_uuid)
        SECURITY_LOGGER.warning(f"Node blocked: {node_uuid} - Reason: {reason}")
        
    def remove_blocked_node(self, node_uuid: str):
        """Remove a node from the blocklist."""
        self.blocked_nodes.discard(node_uuid)
        SECURITY_LOGGER.info(f"Node unblocked: {node_uuid}")
        
    def add_blocked_ip(self, ip_address: str, reason: str = "Manual block"):
        """Add an IP to the blocklist."""
        self.blocked_ips.add(ip_address)
        SECURITY_LOGGER.warning(f"IP blocked: {ip_address} - Reason: {reason}")
        
    def remove_blocked_ip(self, ip_address: str):
        """Remove an IP from the blocklist."""
        self.blocked_ips.discard(ip_address)
        SECURITY_LOGGER.info(f"IP unblocked: {ip_address}")
        
    def get_security_stats(self) -> Dict[str, Any]:
        """Get current security statistics."""
        return {
            "security_enabled": self.security_enabled,
            "authenticated_nodes": len(self.authenticated_nodes),
            "blocked_nodes": len(self.blocked_nodes),
            "blocked_ips": len(self.blocked_ips),
            "allowed_nodes": len(self.allowed_nodes) if self.allowed_nodes else "unlimited",
            "active_connections": sum(self.connection_counts.values()),
            "authentication_required": REQUIRE_NODE_AUTHENTICATION,
            "message_signing_enabled": ENABLE_MESSAGE_SIGNING,
            "reject_unsigned_messages": REJECT_UNSIGNED_MESSAGES
        }
        
    def log_security_event(self, event_type: str, details: str, severity: str = "info"):
        """Log a security event."""
        log_method = getattr(SECURITY_LOGGER, severity.lower(), SECURITY_LOGGER.info)
        log_method(f"{event_type}: {details}")


# Global security manager instance
SECURITY_MANAGER = SecurityManager()
