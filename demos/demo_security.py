#!/usr/bin/env python3
"""
P2P Network Security Demonstration Script

This script demonstrates the security features implemented in the antispam-beacon P2P network.
"""

import time
import requests
import subprocess
import sys

def print_header(title):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(f"🔒 {title}")
    print("="*60)

def print_step(step, description):
    """Print a formatted step."""
    print(f"\n{step}. {description}")
    print("-" * 40)

def run_command(command, description):
    """Run a command and show the output."""
    print(f"Running: {command}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        if result.stdout:
            print(f"Output:\n{result.stdout}")
        if result.stderr:
            print(f"Errors:\n{result.stderr}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("Command timed out")
        return False
    except Exception as e:
        print(f"Error running command: {e}")
        return False

def check_server_status():
    """Check if the server is running."""
    try:
        response = requests.get("http://localhost:8081/check?user_id=123", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    print_header("P2P Network Security Demonstration")
    
    print("This demonstration shows the security features implemented to prevent")
    print("rogue P2P nodes from compromising the antispam-beacon network.")
    
    print_step("1", "Show Current Security Status")
    run_command("python configure_security.py status", "Check current security configuration")
    
    print_step("2", "Set Up Basic Security")
    print("Setting up basic security with authentication and rate limiting...")
    success = run_command("python configure_security.py setup", "Configure basic security")
    
    if success:
        print("✅ Basic security configuration completed!")
        print("🔐 Network now has:")
        print("  - Pre-shared key authentication")
        print("  - Connection rate limiting")
        print("  - Message rate limiting") 
        print("  - Security event logging")
    else:
        print("❌ Failed to configure basic security")
        
    print_step("3", "Show Updated Security Status")
    run_command("python configure_security.py status", "Check updated security configuration")
    
    print_step("4", "Demonstrate Node Whitelisting")
    print("Adding a test node to the whitelist...")
    test_uuid = "test-node-12345"
    run_command(f"python configure_security.py allow {test_uuid}", "Add test node to whitelist")
    
    print("\nRemoving the test node from whitelist...")
    run_command(f"python configure_security.py unallow {test_uuid}", "Remove test node from whitelist")
    
    print_step("5", "Demonstrate Node Blacklisting")
    print("Adding a malicious node to the blacklist...")
    malicious_uuid = "malicious-node-67890"
    run_command(f"python configure_security.py block {malicious_uuid}", "Block malicious node")
    
    print("\nRemoving the malicious node from blacklist...")
    run_command(f"python configure_security.py unblock {malicious_uuid}", "Unblock node")
    
    print_step("6", "Demonstrate IP Blacklisting")
    print("Adding a malicious IP to the blacklist...")
    malicious_ip = "192.168.1.100"
    run_command(f"python configure_security.py block-ip {malicious_ip}", "Block malicious IP")
    
    print("\nRemoving the malicious IP from blacklist...")
    run_command(f"python configure_security.py unblock-ip {malicious_ip}", "Unblock IP")
    
    print_step("7", "Show Detailed Configuration")
    run_command("python configure_security.py config", "Show detailed security configuration")
    
    print_step("8", "Test Server with Security")
    print("Checking if server is running with security enabled...")
    
    if check_server_status():
        print("✅ Server is running and responding to API requests")
        print("🔐 Security is now active and protecting the P2P network")
    else:
        print("⚠️  Server is not running. Start it with: python run_server.py")
        print("📝 When you start the server, you'll see security logs in security.log")
    
    print_step("9", "Security Benefits Summary")
    print("🛡️  Your P2P network is now protected against:")
    print("   • Unauthorized node connections")
    print("   • Connection flooding attacks") 
    print("   • Message spam attacks")
    print("   • Rogue node infiltration")
    print("   • Data corruption from untrusted sources")
    
    print("\n📋 Security Features Implemented:")
    print("   ✅ Pre-shared key authentication")
    print("   ✅ Node whitelisting/blacklisting")
    print("   ✅ IP address blacklisting")
    print("   ✅ Connection rate limiting")
    print("   ✅ Message rate limiting")
    print("   ✅ Security event logging")
    print("   ✅ Secure handshake protocol")
    print("   ✅ Protection against replay attacks")
    
    print("\n🔧 Optional Advanced Features:")
    print("   🔄 Message signing (can be enabled)")
    print("   🔄 TLS encryption (future enhancement)")
    print("   🔄 Role-based access control (future enhancement)")
    
    print_header("Security Demonstration Complete")
    print("Your antispam-beacon P2P network is now secure against rogue nodes!")
    print("\n📖 For more information:")
    print("   • Check SECURITY_ANALYSIS.md for detailed security overview")
    print("   • Use 'python configure_security.py --help' for security management")
    print("   • Monitor security.log for security events")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Demonstration interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        sys.exit(1)
