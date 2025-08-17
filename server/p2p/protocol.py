"""P2P Protocol for handling connections and data exchange."""

# SPDX-License-Identifier: MIT
# -*- coding: utf-8 -*-
# server/p2p/protocol.py

import json
import time
from twisted.internet import protocol
from twisted.internet import task, defer
from server.database import retrieve_spammer_data_from_db, delete_spammer_data
from server.server_config import LOGGER
from .config import HANDSHAKE_INIT, HANDSHAKE_RESPONSE, RED_COLOR, GREEN_COLOR
from .config import YELLOW_COLOR, INVERSE_COLOR, RESET_COLOR
from .utils import split_json_objects, decode_nested_json
from .security import SECURITY_MANAGER


class P2PProtocol(protocol.Protocol):
    """P2P protocol to handle connections and exchange spammer information."""

    def __init__(self):
        self.processed_data = set()
        self.received_from_peer = None  # Add this attribute
        self.timeout_call = None  # Initialize timeout_call
        self.peer_uuid = None  # Initialize peer_uuid
        self.handshake_complete = False  # Track handshake status

    def connectionMade(self):
        """Handle new P2P connections."""
        peer = self.get_peer()
        
        # Check for configuration changes before processing connection
        SECURITY_MANAGER.check_config_reload()
        
        # Security check: Verify connection is allowed
        allowed, reason = SECURITY_MANAGER.is_connection_allowed(peer.host)
        if not allowed:
            SECURITY_MANAGER.log_security_event(
                "CONNECTION_REJECTED", 
                f"Connection from {peer.host}:{peer.port} rejected: {reason}",
                "warning"
            )
            LOGGER.warning(f"%sConnection rejected from %s:%d - %s%s", 
                          RED_COLOR, peer.host, peer.port, reason, RESET_COLOR)
            self.transport.loseConnection()
            return
            
        # Register the connection for tracking
        SECURITY_MANAGER.register_connection(peer.host, self.peer_uuid)
        
        self.factory.peers.append(peer)
        LOGGER.info(
            "%sP2P connection made with %s:%d%s",
            YELLOW_COLOR,
            peer.host,
            peer.port,
            RESET_COLOR,
        )
        LOGGER.info("%sP2P connection details: %s%s", YELLOW_COLOR, peer, RESET_COLOR)
        self.send_handshake_init()

    def get_peer(self):
        """Override getPeer to return PeerAddress with UUID."""
        peer = self.transport.getPeer()
        peer_uuid = self.peer_uuid if self.peer_uuid else self.factory.node_uuid
        return self.factory.PeerAddress(peer.type, peer.host, peer.port, peer_uuid)

    def send_handshake_init(self):
        """Send handshake initiation message."""
        message = {"type": HANDSHAKE_INIT, "uuid": self.factory.node_uuid}
        
        # Add authentication data if required
        auth_challenge = SECURITY_MANAGER.generate_auth_challenge(self.factory.node_uuid)
        if auth_challenge:
            message.update(auth_challenge)
            
        # Add version information
        message["node_version"] = "1.0.0"
        message["timestamp"] = time.time()
        
        # Sign the message if signing is enabled
        message = SECURITY_MANAGER.sign_message(message, self.factory.node_uuid)
        
        message_json = json.dumps(message)
        self.transport.write(message_json.encode("utf-8"))
        LOGGER.info("Sent handshake initiation: %s", message_json)

    def send_handshake_response(self, node_uuid):
        """Send handshake response message."""
        message = {"type": HANDSHAKE_RESPONSE, "uuid": node_uuid}
        
        # Add authentication data if required
        auth_challenge = SECURITY_MANAGER.generate_auth_challenge(node_uuid)
        if auth_challenge:
            message.update(auth_challenge)
            
        # Add version information
        message["node_version"] = "1.0.0"
        message["timestamp"] = time.time()
        
        # Sign the message if signing is enabled
        message = SECURITY_MANAGER.sign_message(message, node_uuid)
        
        message_json = json.dumps(message)
        self.transport.write(message_json.encode("utf-8"))
        LOGGER.info("Sent handshake response: %s", message_json)

    def dataReceived(self, data):
        """Handle received P2P data."""
        message_string = data.decode("utf-8")
        # Split the message by '}{' and add the braces back
        json_strings = split_json_objects(message_string)

        LOGGER.debug("Number of JSON strings: %d", len(json_strings))
        LOGGER.debug("Split JSON strings: %s", "\n".join(json_strings))

        for json_string in json_strings:
            try:
                message = json.loads(json_string)
                message = decode_nested_json(message)

                # Security: Check if message is allowed
                peer = self.get_peer()
                message_type = message.get("type", "unknown")
                
                allowed, reason = SECURITY_MANAGER.is_message_allowed(
                    peer.host, self.peer_uuid or "unknown", message_type
                )
                if not allowed:
                    SECURITY_MANAGER.log_security_event(
                        "MESSAGE_REJECTED",
                        f"Message from {peer.host}:{peer.port} ({self.peer_uuid}) rejected: {reason}",
                        "warning"
                    )
                    LOGGER.warning(f"%sMessage rejected from %s:%d - %s%s",
                                  RED_COLOR, peer.host, peer.port, reason, RESET_COLOR)
                    continue
                    
                # Security: Verify message signature if enabled
                if not SECURITY_MANAGER.verify_message_signature(message, self.peer_uuid or "unknown"):
                    SECURITY_MANAGER.log_security_event(
                        "INVALID_SIGNATURE",
                        f"Invalid message signature from {peer.host}:{peer.port} ({self.peer_uuid})",
                        "warning"
                    )
                    LOGGER.warning(f"%sInvalid message signature from %s:%d%s",
                                  RED_COLOR, peer.host, peer.port, RESET_COLOR)
                    continue

                self.received_from_peer = (
                    peer  # Store the peer from which the data was received
                )

                LOGGER.debug(
                    "%sP2P message%s from %s:%d (UUID: %s)\n%s",
                    INVERSE_COLOR,
                    RESET_COLOR,
                    peer.host,
                    peer.port,
                    peer.node_uuid,
                    json.dumps(message, indent=4),
                )

                if message_type == HANDSHAKE_INIT:
                    self.handle_handshake_init(message)
                elif message_type == HANDSHAKE_RESPONSE:
                    self.handle_handshake_response(message)
                elif message_type == "check_p2p_data":
                    self.handle_check_p2p_data(message)
                elif message_type == "check_p2p_data_response":
                    self.handle_check_p2p_data_response(message)
                elif message_type == "spammer_info_broadcast":
                    self.handle_p2p_data(message)
                elif message_type == "spammer_info_removal":
                    self.handle_spammer_info_removal(message)
                elif message_type == "unban":
                    self.handle_unban_message(message)
                elif message_type == "gunban":
                    self.handle_gunban_message(message)
                else:
                    SECURITY_MANAGER.log_security_event(
                        "UNKNOWN_MESSAGE_TYPE",
                        f"Unknown message type '{message_type}' from {peer.host}:{peer.port} ({self.peer_uuid})",
                        "warning"
                    )
                    LOGGER.warning(
                        "%sUnknown message type: %s%s",
                        RED_COLOR,
                        message_type,
                        RESET_COLOR,
                    )
            except json.JSONDecodeError as e:
                peer = self.get_peer()
                SECURITY_MANAGER.log_security_event(
                    "JSON_DECODE_ERROR",
                    f"Invalid JSON from {peer.host}:{peer.port}: {e}",
                    "warning"
                )
                LOGGER.error("Failed to decode JSON: %s", e)
                LOGGER.debug(
                    "Received from %s:%d",
                    peer.host,
                    peer.port,
                )
                LOGGER.debug("Received data: %s", message)
            except Exception as e:
                peer = self.get_peer()
                SECURITY_MANAGER.log_security_event(
                    "MESSAGE_PROCESSING_ERROR",
                    f"Error processing message from {peer.host}:{peer.port}: {e}",
                    "error"
                )
                LOGGER.error("Error processing data: %s", e)

    def handle_spammer_info_removal(self, message):
        """Handle spammer info removal message."""
        # Legacy handler - redirect to gunban
        user_id = message.get("user_id")
        if user_id:
            LOGGER.warning("Received legacy spammer_info_removal message for %s, converting to gunban", user_id)
            self.factory.gunban(user_id, source_node_uuid="legacy", exclude=self)
        else:
            LOGGER.warning("User ID missing in legacy spammer removal request")

    def handle_unban_message(self, message):
        """Handle incoming unban message from peer."""
        # Legacy handler - redirect to gunban
        spammer_id = message.get("spammer_id")
        source_node = message.get("source_node_uuid")
        
        if spammer_id:
            LOGGER.warning("Received legacy unban message for %s, converting to gunban", spammer_id)
            self.factory.gunban(spammer_id, source_node_uuid=source_node, exclude=self)
        else:
            LOGGER.warning("Unban message missing spammer_id")

    def handle_gunban_message(self, message):
        """Handle incoming gunban (global unban) message from peer."""
        spammer_id = message.get("spammer_id")
        source_node = message.get("source_node_uuid")
        timestamp = message.get("timestamp")
        
        if not spammer_id:
            LOGGER.warning("GUNBAN: Message missing spammer_id")
            return
        
        if not source_node:
            LOGGER.warning("GUNBAN: Message missing source_node_uuid")
            return
            
        LOGGER.debug("GUNBAN: Received removal request for %s from node %s (timestamp: %s)", 
                    spammer_id, source_node, timestamp)
        
        # Process gunban and propagate to other peers (excluding sender)
        self.factory.gunban(spammer_id, source_node_uuid=source_node, exclude=self)

    def send_unban(self, spammer_id: str, source_node_uuid: str):
        """Send unban message to this peer."""
        # Deprecated method - keeping for backward compatibility
        LOGGER.warning("send_unban is deprecated, gunban messages are sent automatically")
        import time
        import json
        
        message = {
            "type": "gunban",  # Use new unified message type
            "spammer_id": spammer_id,
            "source_node_uuid": source_node_uuid,
            "timestamp": time.time()
        }
        message_json = json.dumps(message)
        self.transport.write(message_json.encode("utf-8"))
        LOGGER.debug("Sent gunban message for %s to peer", spammer_id)

    def handle_handshake_init(self, data):
        """Handle handshake initiation message."""
        peer_uuid = data["uuid"]
        peer = self.get_peer()
        peer.node_uuid = peer_uuid
        self.peer_uuid = peer_uuid  # Store the peer UUID in the protocol instance

        # Security: Authenticate the node if required
        auth_success, auth_reason = SECURITY_MANAGER.authenticate_node(peer_uuid, data)
        if not auth_success:
            SECURITY_MANAGER.log_security_event(
                "AUTHENTICATION_FAILED",
                f"Node {peer_uuid} from {peer.host}:{peer.port} failed authentication: {auth_reason}",
                "warning"
            )
            LOGGER.warning(
                "%sAuthentication failed for %s:%d (UUID: %s) - %s%s",
                RED_COLOR,
                peer.host,
                peer.port,
                peer_uuid,
                auth_reason,
                RESET_COLOR,
            )
            self.transport.loseConnection()
            return

        # Security: Check if connection is still allowed with UUID
        allowed, reason = SECURITY_MANAGER.is_connection_allowed(peer.host, peer_uuid)
        if not allowed:
            SECURITY_MANAGER.log_security_event(
                "CONNECTION_REJECTED_AFTER_AUTH",
                f"Connection from {peer.host}:{peer.port} (UUID: {peer_uuid}) rejected after auth: {reason}",
                "warning"
            )
            LOGGER.warning(
                "%sConnection rejected for %s:%d (UUID: %s) - %s%s",
                RED_COLOR,
                peer.host,
                peer.port,
                peer_uuid,
                reason,
                RESET_COLOR,
            )
            self.transport.loseConnection()
            return

        LOGGER.info(
            "%sReceived handshake initiation from %s:%d (UUID: %s)%s",
            GREEN_COLOR,
            peer.host,
            peer.port,
            peer.node_uuid,
            RESET_COLOR,
        )
        
        if peer.node_uuid == self.factory.node_uuid:
            LOGGER.info(
                "%sDisconnecting self-connection to %s:%d (UUID: %s)%s",
                RED_COLOR,
                peer.host,
                peer.port,
                peer.node_uuid,
                RESET_COLOR,
            )
            self.transport.loseConnection()
        elif self.factory.is_duplicate_uuid(peer_uuid, self):
            LOGGER.info(
                "%sDisconnecting duplicate connection to %s:%d (UUID: %s)%s",
                RED_COLOR,
                peer.host,
                peer.port,
                peer.node_uuid,
                RESET_COLOR,
            )
            self.transport.loseConnection()
        else:
            self.send_handshake_response(self.factory.node_uuid)
            self.handshake_complete = True  # Mark handshake as complete
            self.factory.known_uuids.add(peer_uuid)  # Add UUID to known UUIDs
            
            SECURITY_MANAGER.log_security_event(
                "HANDSHAKE_COMPLETED",
                f"Successful handshake with {peer.host}:{peer.port} (UUID: {peer_uuid})",
                "info"
            )

    def handle_handshake_response(self, data):
        """Handle handshake response message."""
        if self.handshake_complete:
            return  # Ignore further handshake messages

        peer_uuid = data["uuid"]
        peer = self.get_peer()
        peer.node_uuid = peer_uuid
        self.peer_uuid = peer_uuid  # Store the peer UUID in the protocol instance

        # Security: Authenticate the node if required
        auth_success, auth_reason = SECURITY_MANAGER.authenticate_node(peer_uuid, data)
        if not auth_success:
            SECURITY_MANAGER.log_security_event(
                "AUTHENTICATION_FAILED",
                f"Node {peer_uuid} from {peer.host}:{peer.port} failed authentication: {auth_reason}",
                "warning"
            )
            LOGGER.warning(
                "%sAuthentication failed for %s:%d (UUID: %s) - %s%s",
                RED_COLOR,
                peer.host,
                peer.port,
                peer_uuid,
                auth_reason,
                RESET_COLOR,
            )
            self.transport.loseConnection()
            return

        # Security: Check if connection is still allowed with UUID
        allowed, reason = SECURITY_MANAGER.is_connection_allowed(peer.host, peer_uuid)
        if not allowed:
            SECURITY_MANAGER.log_security_event(
                "CONNECTION_REJECTED_AFTER_AUTH",
                f"Connection from {peer.host}:{peer.port} (UUID: {peer_uuid}) rejected after auth: {reason}",
                "warning"
            )
            LOGGER.warning(
                "%sConnection rejected for %s:%d (UUID: %s) - %s%s",
                RED_COLOR,
                peer.host,
                peer.port,
                peer_uuid,
                reason,
                RESET_COLOR,
            )
            self.transport.loseConnection()
            return

        LOGGER.info(
            "%sReceived handshake response from %s:%d (UUID: %s)%s",
            GREEN_COLOR,
            peer.host,
            peer.port,
            peer.node_uuid,
            RESET_COLOR,
        )
        
        if peer.node_uuid == self.factory.node_uuid:
            LOGGER.info(
                "%sDisconnecting self-connection to %s:%d (UUID: %s)%s",
                RED_COLOR,
                peer.host,
                peer.port,
                peer.node_uuid,
                RESET_COLOR,
            )
            self.transport.loseConnection()
        elif self.factory.is_duplicate_uuid(peer_uuid, self):
            LOGGER.info(
                "%sDisconnecting duplicate connection to %s:%d (UUID: %s)%s",
                RED_COLOR,
                peer.host,
                peer.port,
                peer.node_uuid,
                RESET_COLOR,
            )
            self.transport.loseConnection()
        else:
            self.handshake_complete = True  # Mark handshake as complete
            self.factory.known_uuids.add(peer_uuid)  # Add UUID to known UUIDs
            
            SECURITY_MANAGER.log_security_event(
                "HANDSHAKE_COMPLETED",
                f"Successful handshake with {peer.host}:{peer.port} (UUID: {peer_uuid})",
                "info"
            )

    def handle_check_p2p_data(self, data):
        """Handle check_p2p_data request and respond with data if available."""
        user_id = data["user_id"]
        peer = self.get_peer()
        LOGGER.info(
            "%s Received check_p2p_data request from %s:%d (UUID: %s)",
            user_id,
            peer.host,
            peer.port,
            peer.node_uuid,
        )
        spammer_data = retrieve_spammer_data_from_db(user_id)
        if spammer_data:
            # If p2p_data is not available, construct it from other data
            if not spammer_data.get("p2p_data"):
                spammer_data["p2p_data"] = {
                    "lols_bot_data": spammer_data["lols_bot_data"],
                    "cas_chat_data": spammer_data["cas_chat_data"],
                }

            # Parse nested JSON data
            lols_bot_data = spammer_data.get("lols_bot_data", {})
            if isinstance(lols_bot_data, str):
                lols_bot_data = json.loads(lols_bot_data)
            cas_chat_data = spammer_data.get("cas_chat_data", {})
            if isinstance(cas_chat_data, str):
                cas_chat_data = json.loads(cas_chat_data)
            p2p_data = spammer_data.get("p2p_data", {})
            if isinstance(p2p_data, str):
                p2p_data = json.loads(p2p_data)

            response = {
                "type": "check_p2p_data_response",
                "user_id": user_id,
                "lols_bot_data": lols_bot_data,
                "cas_chat_data": cas_chat_data,
                "p2p_data": p2p_data,
                "is_spammer": spammer_data["is_spammer"],
            }
            response_json = json.dumps(response, indent=4)
            self.transport.write(response_json.encode("utf-8"))
            LOGGER.debug("%s sent check_p2p_data response:\n%s", user_id, response_json)
        else:
            response = {
                "type": "check_p2p_data_response",
                "user_id": user_id,
                "error": "No spammer data found",
            }
            response_json = json.dumps(response, indent=4)
            self.transport.write(response_json.encode("utf-8"))
            LOGGER.info(
                "%s No spammer data found, sent response:\n%s", user_id, response_json
            )

    def handle_check_p2p_data_response(self, data):
        """Handle check_p2p_data_response and resolve the deferred."""
        user_id = data["user_id"]
        peer = self.get_peer()
        LOGGER.info(
            "%s Received check_p2p_data_response from %s:%d",
            user_id,
            peer.host,
            peer.port,
        )
        if hasattr(self, "deferred"):
            if "error" in data:
                self.deferred.callback(None)
            else:
                self.deferred.callback(json.dumps(data))
            if self.timeout_call:
                if (
                    isinstance(self.timeout_call, task.DelayedCall)
                    and self.timeout_call.active()
                ):
                    self.timeout_call.cancel()
                elif isinstance(self.timeout_call, defer.Deferred):
                    pass  # It's already handled by connectionLost
            del self.deferred

    def handle_p2p_data(self, data):
        """Handle received P2P data."""
        peer = self.get_peer()
        LOGGER.debug("Handling P2P data from %s:%d", peer.host, peer.port)
        if "user_id" in data:
            user_id = data["user_id"]
            data_hash = self.get_data_hash(data)
            if data_hash in self.processed_data:
                LOGGER.debug("%s Data already processed", user_id)
                return
            self.processed_data.add(data_hash)
            lols_bot_data = data.get("lols_bot_data", {})
            if isinstance(lols_bot_data, str):
                lols_bot_data = json.loads(lols_bot_data)
            cas_chat_data = data.get("cas_chat_data", {})
            if isinstance(cas_chat_data, str):
                cas_chat_data = json.loads(cas_chat_data)
            p2p_data = data.get("p2p_data", {})
            if isinstance(p2p_data, str):
                p2p_data = json.loads(p2p_data)
            is_spammer = data.get("is_spammer", False)

            # Retrieve existing data from the database
            existing_data = retrieve_spammer_data_from_db(user_id)
            if existing_data:
                existing_lols_bot_data = existing_data.get("lols_bot_data", {})
                if isinstance(existing_lols_bot_data, str):
                    existing_lols_bot_data = json.loads(existing_lols_bot_data)
                existing_cas_chat_data = existing_data.get("cas_chat_data", {})
                if isinstance(existing_cas_chat_data, str):
                    existing_cas_chat_data = json.loads(existing_cas_chat_data)
                existing_p2p_data = existing_data.get("p2p_data", {})
                if isinstance(existing_p2p_data, str):
                    existing_p2p_data = json.loads(existing_p2p_data)
                existing_is_spammer = existing_data.get("is_spammer", False)

                # Compare new data with existing data
                if (
                    lols_bot_data == existing_lols_bot_data
                    and cas_chat_data == existing_cas_chat_data
                    and is_spammer == existing_is_spammer
                    and p2p_data == existing_p2p_data
                ):
                    LOGGER.debug(
                        "%s Data is the same as existing data, skipping storage",
                        user_id,
                    )
                    return

            # Store the new data
            LOGGER.debug("%s Storing new data", user_id)
            self.factory.store_spammer_data(
                user_id,
                json.dumps(lols_bot_data),
                json.dumps(cas_chat_data),
                json.dumps(p2p_data),
                is_spammer,
            )
            self.factory.broadcast_spammer_info(user_id)
        elif "peers" in data:
            LOGGER.debug("Updating peer list: %s", data["peers"])
            self.factory.update_peer_list(data["peers"])

    def get_data_hash(self, data):
        """Generate a hash for the data to avoid rebroadcasting the same data."""
        return hash(json.dumps(data, sort_keys=True))

    def connectionLost(self, reason=protocol.connectionDone):
        """Handle lost P2P connections."""
        peer = self.get_peer()
        LOGGER.warning(
            "(Host: %s, Port: %s, UUID: %s%s%s) P2P connection lost:\n%s",
            peer.host,
            peer.port,
            YELLOW_COLOR,
            peer.node_uuid,
            RESET_COLOR,
            reason,
        )
        
        # Security: Unregister the connection
        SECURITY_MANAGER.unregister_connection(peer.host, self.peer_uuid)
        
        self.factory.peers = [
            p for p in self.factory.peers if p.host != peer.host or p.port != peer.port
        ]
        if hasattr(self, "deferred"):
            try:
                self.deferred.errback(reason)
            except defer.AlreadyCalledError:
                LOGGER.warning(
                    "Deferred for connection %s:%d already called.",
                    peer.host,
                    peer.port,
                )
            finally:
                del self.deferred

        if not self.factory.peers:
            self.factory.reconnect_to_bootstrap()
