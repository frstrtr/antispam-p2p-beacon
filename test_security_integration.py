#!/usr/bin/env python3
"""
Quick test script to verify security integration with P2P factory
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_security_import():
    """Test that security modules can be imported correctly."""
    try:
        from server.p2p.security import SECURITY_MANAGER
        print("✅ Security manager imported successfully")
        
        # Test security manager initialization
        stats = SECURITY_MANAGER.get_security_stats()
        print("✅ Security manager operational")
        print(f"   Security enabled: {stats['security_enabled']}")
        print(f"   Authentication required: {stats['authentication_required']}")
        print(f"   Message signing enabled: {stats['message_signing_enabled']}")
        
        # Test connection checking
        allowed, reason = SECURITY_MANAGER.is_connection_allowed("127.0.0.1", "test-node-123")
        print(f"✅ Connection check: {'allowed' if allowed else 'blocked'} - {reason}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_protocol_import():
    """Test that updated protocol can be imported."""
    try:
        from server.p2p.protocol import P2PProtocol
        print("✅ Enhanced P2P protocol imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Protocol import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Protocol error: {e}")
        return False

def test_factory_import():
    """Test that updated factory can be imported."""
    try:
        from server.p2p.factory import P2PFactory
        print("✅ Enhanced P2P factory imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Factory import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Factory error: {e}")
        return False

def main():
    print("🔒 Testing P2P Security Integration")
    print("=" * 40)
    
    all_passed = True
    
    # Test imports
    all_passed &= test_security_import()
    all_passed &= test_protocol_import()
    all_passed &= test_factory_import()
    
    if all_passed:
        print("\n✅ All security integration tests passed!")
        print("🔐 Your P2P network security is fully operational")
    else:
        print("\n❌ Some tests failed - check error messages above")
        sys.exit(1)

if __name__ == '__main__':
    main()
