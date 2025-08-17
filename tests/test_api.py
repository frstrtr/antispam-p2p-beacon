#!/usr/bin/env python3
"""
Test suite for Antispam Beacon Server API.

This module contains unit tests for the HTTP REST API endpoints.
"""

import unittest
import requests
import json
import time
import subprocess
import signal
import os
import sys

class TestAntispamBeaconAPI(unittest.TestCase):
    """Test cases for the Antispam Beacon API."""
    
    BASE_URL = "http://localhost:8081"
    server_process = None
    
    @classmethod
    def setUpClass(cls):
        """Start the server before running tests."""
        print("Starting Antispam Beacon Server for testing...")
        # Note: In real testing, you would start the server in a test mode
        # For this example, we assume the server is already running
        pass
    
    @classmethod
    def tearDownClass(cls):
        """Stop the server after tests."""
        if cls.server_process:
            cls.server_process.terminate()
            cls.server_process.wait()
    
    def test_check_clean_user(self):
        """Test checking a user that is not a spammer."""
        test_user_id = "123456789"  # Numeric user ID
        
        # First, ensure user is not in database (unban if exists)
        requests.post(f"{self.BASE_URL}/unban", json={"user_id": test_user_id})
        
        # Check user status
        response = requests.get(f"{self.BASE_URL}/check?user_id={test_user_id}")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertFalse(data.get("is_spammer", True))
        self.assertEqual(data.get("user_id"), test_user_id)
    
    def test_report_and_check_spammer(self):
        """Test reporting a spammer and then checking their status."""
        test_user_id = "987654321"  # Numeric user ID
        test_reason = "automated_test_spam"
        
        # Report the user as spammer
        report_data = {
            "user_id": test_user_id,
            "reason": test_reason
        }
        response = requests.post(f"{self.BASE_URL}/report_id", json=report_data)
        self.assertEqual(response.status_code, 200)
        
        result = response.json()
        self.assertTrue(result.get("success", False))
        
        # Check that user is now flagged
        response = requests.get(f"{self.BASE_URL}/check?user_id={test_user_id}")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data.get("is_spammer", False))
        self.assertEqual(data.get("user_id"), test_user_id)
    
    def test_unban_user(self):
        """Test unbanning a user."""
        test_user_id = "555666777"  # Numeric user ID
        
        # First report the user
        report_data = {
            "user_id": test_user_id,
            "reason": "test_for_unban"
        }
        requests.post(f"{self.BASE_URL}/report_id", json=report_data)
        
        # Then unban the user
        unban_data = {"user_id": test_user_id}
        response = requests.post(f"{self.BASE_URL}/unban", json=unban_data)
        self.assertEqual(response.status_code, 200)
        
        result = response.json()
        self.assertTrue(result.get("success", False))
        self.assertTrue(result.get("found", False))
        
        # Verify user is no longer flagged
        response = requests.get(f"{self.BASE_URL}/check?user_id={test_user_id}")
        data = response.json()
        self.assertFalse(data.get("is_spammer", True))
    
    def test_legacy_remove_id(self):
        """Test the legacy remove_id endpoint."""
        test_user_id = "111222333"  # Numeric user ID
        
        # Report user first
        report_data = {
            "user_id": test_user_id,
            "reason": "test_legacy_removal"
        }
        requests.post(f"{self.BASE_URL}/report_id", json=report_data)
        
        # Use legacy endpoint to remove
        remove_data = {"user_id": test_user_id}
        response = requests.post(f"{self.BASE_URL}/remove_id", json=remove_data)
        self.assertEqual(response.status_code, 200)
        
        # Should behave same as unban
        result = response.json()
        self.assertTrue(result.get("success", False))
    
    def test_invalid_requests(self):
        """Test various invalid request scenarios."""
        # Missing user_id in check
        response = requests.get(f"{self.BASE_URL}/check")
        self.assertNotEqual(response.status_code, 200)
        
        # Invalid JSON in report
        response = requests.post(f"{self.BASE_URL}/report_id", 
                               data="invalid json",
                               headers={"Content-Type": "application/json"})
        self.assertNotEqual(response.status_code, 200)
        
        # Missing user_id in unban
        response = requests.post(f"{self.BASE_URL}/unban", json={})
        self.assertNotEqual(response.status_code, 200)

def run_tests():
    """Run the test suite."""
    print("Antispam Beacon API Test Suite")
    print("=" * 50)
    print("Note: Make sure the server is running on localhost:8081")
    print()
    
    # Check if server is accessible
    try:
        requests.get("http://localhost:8081/check?user_id=12345")
        print("✅ Server is accessible")
    except requests.RequestException:
        print("❌ Server is not accessible. Please start the server first:")
        print("   python server/prime_radiant.py")
        return False    # Run tests
    unittest.main(verbosity=2, exit=False)
    return True

if __name__ == "__main__":
    run_tests()
