#!/usr/bin/env python3
"""
Test script for the gunban (global unban) endpoint.
This demonstrates how to use the unified unban functionality.
"""

import json
import requests

def test_gunban_endpoint():
    """Test the unified gunban endpoint."""
    
    # First, let's add a test spammer (assuming we have report_id endpoint)
    test_spammer_id = "test_user_123"
    
    print(f"Testing GUNBAN (Global Unban) functionality for spammer ID: {test_spammer_id}")
    
    # Test 1: Gunban using JSON POST body
    print("\nTest 1: Gunban with JSON body")
    try:
        response = requests.post(
            "http://localhost:8081/unban",
            json={"spammer_id": test_spammer_id},
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except requests.exceptions.ConnectionError:
        print("Server not running on localhost:8081")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Gunban using form parameters (fallback method)
    print("\nTest 2: Gunban with form parameters")
    try:
        response = requests.post(
            "http://localhost:8081/unban",
            data={"user_id": test_spammer_id}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except requests.exceptions.ConnectionError:
        print("Server not running on localhost:8081")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Error cases
    print("\nTest 3: Error case - missing spammer_id")
    try:
        response = requests.post(
            "http://localhost:8081/unban",
            json={}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except requests.exceptions.ConnectionError:
        print("Server not running on localhost:8081")
    except Exception as e:
        print(f"Error: {e}")

    # Test 4: Test legacy remove_id endpoint (should also use gunban internally)
    print("\nTest 4: Legacy remove_id endpoint")
    try:
        response = requests.post(
            "http://localhost:8081/remove_id",
            data={"user_id": test_spammer_id}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except requests.exceptions.ConnectionError:
        print("Server not running on localhost:8081")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_gunban_endpoint()
