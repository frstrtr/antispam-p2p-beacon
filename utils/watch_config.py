#!/usr/bin/env python3
"""
Automatic file watcher for security configuration.
Monitors .env file for changes and triggers automatic reload.
"""

import os
import time
import sys
import signal
from pathlib import Path

# Add project to path
sys.path.insert(0, '/home/user0/antispam-beacon')

class ConfigWatcher:
    """Watch configuration file for changes and trigger reloads."""
    
    def __init__(self, config_file=".env", check_interval=1.0):
        self.config_file = config_file
        self.check_interval = check_interval
        self.last_mtime = 0
        self.running = False
        
        # Change to project directory
        os.chdir('/home/user0/antispam-beacon')
        
    def get_file_mtime(self):
        """Get file modification time."""
        try:
            return os.path.getmtime(self.config_file)
        except OSError:
            return 0
    
    def trigger_reload(self):
        """Trigger security configuration reload."""
        try:
            from server.p2p.security import SECURITY_MANAGER
            
            print(f"🔄 {time.strftime('%H:%M:%S')} - Configuration change detected, reloading...")
            
            old_allowed = len(SECURITY_MANAGER.allowed_node_keys)
            SECURITY_MANAGER.reload_configuration()
            new_allowed = len(SECURITY_MANAGER.allowed_node_keys)
            
            print(f"✅ {time.strftime('%H:%M:%S')} - Reload complete (trusted nodes: {old_allowed} → {new_allowed})")
            return True
            
        except Exception as e:
            print(f"❌ {time.strftime('%H:%M:%S')} - Reload failed: {e}")
            return False
    
    def start_watching(self):
        """Start watching for file changes."""
        print(f"👁️  Starting configuration watcher for {self.config_file}")
        print(f"   Check interval: {self.check_interval}s")
        print(f"   Press Ctrl+C to stop")
        print("=" * 50)
        
        self.running = True
        self.last_mtime = self.get_file_mtime()
        
        if self.last_mtime == 0:
            print(f"⚠️  Warning: {self.config_file} not found")
        else:
            print(f"📄 Initial file time: {time.ctime(self.last_mtime)}")
        
        try:
            while self.running:
                current_mtime = self.get_file_mtime()
                
                if current_mtime > self.last_mtime:
                    self.trigger_reload()
                    self.last_mtime = current_mtime
                
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            print(f"\n🛑 Watcher stopped by user")
        except Exception as e:
            print(f"\n❌ Watcher error: {e}")
        finally:
            self.running = False
    
    def stop_watching(self):
        """Stop watching for changes."""
        self.running = False

def signal_handler(sig, frame):
    """Handle interrupt signals."""
    print(f"\n🛑 Received signal {sig}, stopping watcher...")
    sys.exit(0)

def main():
    """Main function."""
    # Handle signals
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Parse arguments
    check_interval = 1.0
    if len(sys.argv) > 1:
        try:
            check_interval = float(sys.argv[1])
        except ValueError:
            print(f"❌ Invalid interval: {sys.argv[1]}")
            print("Usage: python watch_config.py [interval_seconds]")
            sys.exit(1)
    
    # Create and start watcher
    watcher = ConfigWatcher(check_interval=check_interval)
    watcher.start_watching()

if __name__ == "__main__":
    main()
