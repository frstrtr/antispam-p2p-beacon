#!/usr/bin/env python3
"""
Security configuration reload utility.
Provides manual reload capability for the P2P security system.
"""

import os
import json
import time
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, '/home/user0/antispam-beacon')

def reload_security_config():
    """Trigger a manual reload of security configuration."""
    try:
        # Import the security manager
        from server.p2p.security import SECURITY_MANAGER
        
        print("🔄 Triggering security configuration reload...")
        
        # Get current config state
        old_allowed = len(SECURITY_MANAGER.allowed_node_keys)
        old_blocked = len(SECURITY_MANAGER.blocked_node_keys)
        
        # Trigger reload
        SECURITY_MANAGER.reload_configuration()
        
        # Show new state
        new_allowed = len(SECURITY_MANAGER.allowed_node_keys)
        new_blocked = len(SECURITY_MANAGER.blocked_node_keys)
        
        print(f"✅ Configuration reloaded successfully!")
        print(f"   Allowed nodes: {old_allowed} → {new_allowed}")
        print(f"   Blocked nodes: {old_blocked} → {new_blocked}")
        print(f"   Security enabled: {SECURITY_MANAGER.enabled}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error importing security manager: {e}")
        print("   Make sure the server components are properly installed")
        return False
    except Exception as e:
        print(f"❌ Error during reload: {e}")
        return False

def check_config_file():
    """Check the current configuration file state."""
    env_file = ".env"
    
    if not os.path.exists(env_file):
        print(f"⚠️  Configuration file {env_file} not found")
        return False
    
    try:
        mtime = os.path.getmtime(env_file)
        print(f"📄 Configuration file: {env_file}")
        print(f"   Last modified: {time.ctime(mtime)}")
        print(f"   Size: {os.path.getsize(env_file)} bytes")
        
        # Show trusted nodes from .env
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        trusted_line = None
        for line in content.split('\n'):
            if line.startswith('ALLOWED_NODE_KEYS='):
                trusted_line = line
                break
        
        if trusted_line:
            trusted_nodes = trusted_line.split('=')[1].strip().strip('"\'')
            if trusted_nodes:
                nodes = [node.strip() for node in trusted_nodes.split(',') if node.strip()]
                print(f"   Trusted nodes in config: {len(nodes)}")
                for node in nodes:
                    print(f"     • {node}")
            else:
                print("   No trusted nodes configured")
        else:
            print("   ALLOWED_NODE_KEYS not found in config")
            
        return True
        
    except Exception as e:
        print(f"❌ Error reading config file: {e}")
        return False

def show_usage():
    """Show usage information."""
    print("Security Configuration Reload Utility")
    print("=" * 50)
    print()
    print("Usage:")
    print("  python reload_security.py [command]")
    print()
    print("Commands:")
    print("  reload     - Trigger configuration reload")
    print("  check      - Check configuration file status")
    print("  status     - Show current security status")
    print("  help       - Show this help message")
    print()
    print("Examples:")
    print("  python reload_security.py reload")
    print("  python reload_security.py check")

def show_status():
    """Show current security status."""
    try:
        from server.p2p.security import SECURITY_MANAGER
        
        print("🔒 Current Security Status")
        print("=" * 30)
        print(f"Security enabled: {SECURITY_MANAGER.enabled}")
        print(f"Authentication required: {SECURITY_MANAGER.require_authentication}")
        print(f"Message signing enabled: {SECURITY_MANAGER.enable_message_signing}")
        print(f"Allowed nodes: {len(SECURITY_MANAGER.allowed_node_keys)}")
        print(f"Blocked nodes: {len(SECURITY_MANAGER.blocked_node_keys)}")
        print(f"Blocked IPs: {len(SECURITY_MANAGER.blocked_ips)}")
        print(f"Max connections per IP: {SECURITY_MANAGER.max_connections_per_ip}")
        
        if SECURITY_MANAGER.allowed_node_keys:
            print("\nAllowed nodes:")
            for node in sorted(SECURITY_MANAGER.allowed_node_keys):
                print(f"  • {node}")
                
        return True
        
    except ImportError as e:
        print(f"❌ Error importing security manager: {e}")
        return False
    except Exception as e:
        print(f"❌ Error getting status: {e}")
        return False

def main():
    """Main function."""
    if len(sys.argv) < 2:
        command = "status"
    else:
        command = sys.argv[1].lower()
    
    # Change to project directory
    os.chdir('/home/user0/antispam-beacon')
    
    if command == "reload":
        success = reload_security_config()
        sys.exit(0 if success else 1)
        
    elif command == "check":
        success = check_config_file()
        sys.exit(0 if success else 1)
        
    elif command == "status":
        success = show_status()
        sys.exit(0 if success else 1)
        
    elif command in ["help", "-h", "--help"]:
        show_usage()
        sys.exit(0)
        
    else:
        print(f"❌ Unknown command: {command}")
        print()
        show_usage()
        sys.exit(1)

if __name__ == "__main__":
    main()
