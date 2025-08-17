#!/usr/bin/env python3
"""
Production-ready Antispam Bot Integration Example
 
This example demonstrates the best practice for integrating a local antispam bot
with the antispam-beacon P2P network using the HTTP REST API.
"""

import requests
import json
import time
import logging
from typing import Optional, Dict, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('AntispamBot')

class AntispamBeaconClient:
    """
    Production-ready client for antispam-beacon server integration.
    
    This client provides robust communication with the antispam-beacon server
    for reporting spammers and checking user status.
    """
    
    def __init__(self, base_url: str = "http://localhost:8081", timeout: int = 5):
        """
        Initialize the beacon client.
        
        Args:
            base_url: Base URL of the antispam-beacon server
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = self._create_robust_session()
        logger.info(f"Initialized AntispamBeaconClient for {base_url}")
    
    def _create_robust_session(self) -> requests.Session:
        """Create HTTP session with retry logic and proper configuration."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            respect_retry_after_header=True
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update({
            'User-Agent': 'AntispamBot/1.0',
            'Content-Type': 'application/json'
        })
        
        session.timeout = self.timeout
        return session
    
    def report_spammer(self, user_id: str, reason: str = "spam_detected", 
                      metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Report a spammer to the P2P network.
        
        Args:
            user_id: Telegram user ID or username to report
            reason: Reason for reporting (e.g., "promotional_spam", "scam")
            metadata: Optional additional metadata about the spam
            
        Returns:
            bool: True if successfully reported, False otherwise
        """
        try:
            # Ensure user_id is numeric for Telegram compatibility
            if user_id.isdigit():
                user_id = str(int(user_id))  # Normalize numeric IDs
            
            payload = {
                "user_id": user_id,
                "reason": reason,
                "source": "local_antispam_bot",
                "timestamp": int(time.time())
            }
            
            if metadata:
                payload["metadata"] = metadata
            
            logger.info(f"Reporting spammer {user_id} with reason: {reason}")
            
            response = self.session.post(
                f"{self.base_url}/report_id",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    logger.info(f"✅ Successfully reported spammer {user_id}")
                    logger.debug(f"Server response: {result}")
                    return True
                else:
                    logger.warning(f"❌ Server returned non-success status: {result}")
                    return False
            else:
                logger.error(f"❌ HTTP error {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error reporting spammer {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error reporting spammer {user_id}: {e}")
            return False
    
    def check_spammer(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Check if a user is flagged as a spammer.
        
        Args:
            user_id: Telegram user ID or username to check
            
        Returns:
            Dict with spammer information or None if error occurred
        """
        try:
            # Normalize user ID
            if user_id.isdigit():
                user_id = str(int(user_id))
            
            logger.debug(f"Checking spammer status for user {user_id}")
            
            response = self.session.get(
                f"{self.base_url}/check",
                params={"user_id": user_id}
            )
            
            if response.status_code == 200:
                result = response.json()
                is_spammer = result.get("is_spammer", False)
                
                if is_spammer:
                    logger.info(f"🚨 User {user_id} is flagged as spammer")
                else:
                    logger.debug(f"✅ User {user_id} is clean")
                
                return result
            else:
                logger.error(f"❌ HTTP error {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error checking user {user_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error checking user {user_id}: {e}")
            return None
    
    def unban_user(self, user_id: str, reason: str = "false_positive") -> bool:
        """
        Remove a user from the spammer database (global unban).
        
        Args:
            user_id: User ID to unban
            reason: Reason for unbanning
            
        Returns:
            bool: True if successfully unbanned, False otherwise
        """
        try:
            if user_id.isdigit():
                user_id = str(int(user_id))
            
            payload = {
                "spammer_id": user_id,
                "reason": reason,
                "source": "local_antispam_bot"
            }
            
            logger.info(f"Unbanning user {user_id} with reason: {reason}")
            
            response = self.session.post(
                f"{self.base_url}/unban",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    logger.info(f"✅ Successfully unbanned user {user_id}")
                    return True
                else:
                    logger.warning(f"❌ Unban failed: {result}")
                    return False
            else:
                logger.error(f"❌ HTTP error {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error unbanning user {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error unbanning user {user_id}: {e}")
            return False
    
    def health_check(self) -> bool:
        """
        Check if the antispam-beacon server is healthy and responding.
        
        Returns:
            bool: True if server is healthy, False otherwise
        """
        try:
            # Use a test user ID to check server responsiveness
            response = self.session.get(
                f"{self.base_url}/check",
                params={"user_id": "999999999"},
                timeout=3
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok") is True:
                    logger.debug("✅ Server health check passed")
                    return True
            
            logger.warning(f"❌ Server health check failed: {response.status_code}")
            return False
            
        except Exception as e:
            logger.error(f"❌ Server health check error: {e}")
            return False


class LocalAntispamBot:
    """
    Example local antispam bot implementation.
    
    This demonstrates how to integrate spam detection with the beacon client
    for automatic P2P network propagation.
    """
    
    def __init__(self, beacon_url: str = "http://localhost:8081"):
        """Initialize the antispam bot."""
        self.beacon = AntispamBeaconClient(beacon_url)
        self.spam_confidence_threshold = 0.8
        logger.info("Initialized LocalAntispamBot")
    
    def analyze_message(self, message: str, user_id: str) -> tuple[bool, float, str]:
        """
        Analyze a message for spam content.
        
        This is a simplified example - replace with your actual ML model
        or rule-based detection system.
        
        Args:
            message: Message content to analyze
            user_id: User ID who sent the message
            
        Returns:
            Tuple of (is_spam, confidence, reason)
        """
        # Simple rule-based detection (replace with your logic)
        spam_keywords = [
            'crypto', 'bitcoin', 'investment', 'profit', 'earn money',
            'click here', 'limited time', 'act now', 'guaranteed',
            'make money fast', 'work from home'
        ]
        
        message_lower = message.lower()
        detected_keywords = [kw for kw in spam_keywords if kw in message_lower]
        
        if detected_keywords:
            confidence = min(0.9, len(detected_keywords) * 0.3)
            reason = f"promotional_content_keywords: {', '.join(detected_keywords)}"
            return True, confidence, reason
        
        # Check for excessive links
        if message.count('http') > 2:
            return True, 0.7, "excessive_links"
        
        # Check for excessive caps
        if len(message) > 10 and sum(c.isupper() for c in message) / len(message) > 0.7:
            return True, 0.6, "excessive_caps"
        
        return False, 0.1, "clean_content"
    
    def handle_message(self, user_id: str, message: str, chat_id: str = None) -> Dict[str, Any]:
        """
        Handle an incoming message with spam detection and network reporting.
        
        Args:
            user_id: User ID who sent the message
            message: Message content
            chat_id: Optional chat ID where message was sent
            
        Returns:
            Dict with processing results
        """
        result = {
            "user_id": user_id,
            "action": "none",
            "is_spam": False,
            "confidence": 0.0,
            "reason": "",
            "network_reported": False
        }
        
        try:
            # First check if user is already known spammer
            known_spammer = self.beacon.check_spammer(user_id)
            if known_spammer and known_spammer.get("is_spammer"):
                logger.info(f"🚨 User {user_id} is already flagged as spammer")
                result.update({
                    "action": "block_known_spammer",
                    "is_spam": True,
                    "confidence": 1.0,
                    "reason": "known_spammer_in_network"
                })
                return result
            
            # Analyze message content
            is_spam, confidence, reason = self.analyze_message(message, user_id)
            
            result.update({
                "is_spam": is_spam,
                "confidence": confidence,
                "reason": reason
            })
            
            if is_spam and confidence >= self.spam_confidence_threshold:
                # Report to P2P network
                metadata = {
                    "message_sample": message[:100],  # First 100 chars
                    "chat_id": chat_id,
                    "detection_method": "rule_based",
                    "confidence": confidence
                }
                
                success = self.beacon.report_spammer(user_id, reason, metadata)
                result["network_reported"] = success
                
                if success:
                    result["action"] = "reported_and_blocked"
                    logger.info(f"✅ Spammer {user_id} reported to P2P network")
                else:
                    result["action"] = "local_block_only"
                    logger.warning(f"❌ Failed to report spammer {user_id} to network")
            
            elif is_spam:
                # Low confidence - just log
                result["action"] = "flagged_low_confidence"
                logger.info(f"⚠️ User {user_id} flagged as potential spam (low confidence)")
            
            else:
                # Clean message
                result["action"] = "allowed"
                logger.debug(f"✅ Clean message from user {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Error processing message from {user_id}: {e}")
            result["action"] = "error"
            result["error"] = str(e)
        
        return result
    
    def start_monitoring(self):
        """Start the monitoring loop."""
        logger.info("🚀 Starting antispam bot monitoring")
        
        # Health check
        if not self.beacon.health_check():
            logger.error("❌ Cannot connect to antispam-beacon server")
            return False
        
        logger.info("✅ Connected to antispam-beacon server")
        logger.info("🤖 Bot is ready to process messages")
        return True


def main():
    """Example usage of the antispam bot."""
    # Initialize bot
    bot = LocalAntispamBot()
    
    if not bot.start_monitoring():
        logger.error("Failed to start bot")
        return
    
    # Example message processing
    test_messages = [
        ("user123", "Hello, how are you?", "clean_chat"),
        ("spammer456", "🚀 CRYPTO INVESTMENT OPPORTUNITY! Click here to earn money fast! LIMITED TIME!", "public_chat"),
        ("user789", "Check out this cool link: https://example.com", "tech_chat"),
        ("scammer999", "GUARANTEED PROFIT! Bitcoin trading! Work from home! Act now!", "trading_chat")
    ]
    
    print("\n" + "="*80)
    print("TESTING ANTISPAM BOT MESSAGE PROCESSING")
    print("="*80)
    
    for user_id, message, chat_id in test_messages:
        print(f"\n📥 Processing message from {user_id}:")
        print(f"   Message: {message[:60]}{'...' if len(message) > 60 else ''}")
        print(f"   Chat: {chat_id}")
        
        result = bot.handle_message(user_id, message, chat_id)
        
        print(f"   📊 Result: {result['action']}")
        if result['is_spam']:
            print(f"   🚨 Spam detected (confidence: {result['confidence']:.2f})")
            print(f"   📝 Reason: {result['reason']}")
            if result['network_reported']:
                print(f"   🌐 Reported to P2P network: ✅")
            else:
                print(f"   🌐 Reported to P2P network: ❌")
        else:
            print(f"   ✅ Clean message")
        
        time.sleep(1)  # Small delay between tests
    
    print(f"\n{'='*80}")
    print("✅ Testing completed")


if __name__ == "__main__":
    main()
