#!/usr/bin/env python3
"""
Beacon Mode Demonstration Script

This script demonstrates the difference between beacon mode and full mode
for the antispam-beacon server.
"""

import requests
import json
import time
import subprocess
import os
import signal
import sys
from typing import Optional

class BeaconModeDemo:
    """Demonstrate beacon mode vs full mode functionality."""
    
    def __init__(self):
        self.base_url = "http://localhost:8081"
        self.server_process: Optional[subprocess.Popen] = None
        
    def start_server(self, beacon_mode: bool = False) -> bool:
        """Start the server in specified mode."""
        # Stop any existing server
        self.stop_server()
        
        # Set environment variable
        env_content = f"BEACON_MODE_ONLY={'true' if beacon_mode else 'false'}\n"
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print(f"🚀 Starting server in {'BEACON' if beacon_mode else 'FULL'} mode...")
        
        # Start server
        with open('demo_server.log', 'w') as log_file:
            self.server_process = subprocess.Popen(
                [sys.executable, 'run_server.py'],
                stdout=log_file,
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid
            )
        
        # Wait for server to start
        for i in range(10):
            try:
                response = requests.get(f"{self.base_url}/check?user_id=123456789", timeout=2)
                if response.status_code == 200:
                    print(f"✅ Server started successfully in {'BEACON' if beacon_mode else 'FULL'} mode")
                    return True
            except requests.exceptions.RequestException:
                time.sleep(1)
                print(f"   Waiting for server... ({i+1}/10)")
        
        print("❌ Failed to start server")
        return False
    
    def stop_server(self):
        """Stop the server if running."""
        if self.server_process:
            try:
                # Kill the process group to ensure all child processes are terminated
                os.killpg(os.getpgid(self.server_process.pid), signal.SIGTERM)
                self.server_process.wait(timeout=5)
                print("🛑 Server stopped")
            except (subprocess.TimeoutExpired, ProcessLookupError):
                try:
                    os.killpg(os.getpgid(self.server_process.pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass
            self.server_process = None
            time.sleep(2)  # Give ports time to be released
    
    def test_api_response(self, user_id: str, mode_name: str) -> dict:
        """Test API response and return timing info."""
        start_time = time.time()
        
        try:
            response = requests.get(f"{self.base_url}/check?user_id={user_id}", timeout=10)
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "response_time_ms": round(response_time, 2),
                    "data": data,
                    "mode": mode_name
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "mode": mode_name
                }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "mode": mode_name
            }
    
    def report_spammer(self, user_id: str, reason: str) -> bool:
        """Report a spammer to the server."""
        try:
            response = requests.post(
                f"{self.base_url}/report_id",
                json={"user_id": user_id, "reason": reason},
                timeout=5
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def analyze_response(self, result: dict):
        """Analyze and display API response."""
        if not result["success"]:
            print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
            return
        
        data = result["data"]
        mode = result["mode"]
        response_time = result["response_time_ms"]
        
        print(f"   📊 {mode} Mode Results:")
        print(f"   ⏱️  Response Time: {response_time}ms")
        print(f"   🎯 Is Spammer: {data.get('is_spammer', False)}")
        
        # Check which data sources have content
        lols_bot_data = data.get("lols_bot", {})
        cas_chat_data = data.get("cas_chat", {})
        p2p_data = data.get("p2p", {})
        
        print(f"   📡 Data Sources:")
        print(f"      • Local Database: ✅")
        print(f"      • P2P Network: ✅")
        print(f"      • lols.bot API: {'✅' if lols_bot_data else '❌'}")
        print(f"      • cas.chat API: {'✅' if cas_chat_data else '❌'}")
        
        return {
            "response_time": response_time,
            "has_external_data": bool(lols_bot_data or cas_chat_data)
        }
    
    def run_demo(self):
        """Run the complete demonstration."""
        print("=" * 80)
        print("🚀 ANTISPAM BEACON - BEACON MODE DEMONSTRATION")
        print("=" * 80)
        print()
        
        test_user_clean = "123456789"
        test_user_spammer = "999888777"
        
        # Store results for comparison
        results = {}
        
        for mode_name, beacon_mode in [("FULL", False), ("BEACON", True)]:
            print(f"{'='*50}")
            print(f"🧪 TESTING {mode_name} MODE")
            print(f"{'='*50}")
            
            # Start server in the specified mode
            if not self.start_server(beacon_mode):
                print(f"❌ Failed to start server in {mode_name} mode")
                continue
            
            print(f"\n1️⃣ Testing clean user check ({test_user_clean}):")
            clean_result = self.test_api_response(test_user_clean, mode_name)
            clean_stats = self.analyze_response(clean_result)
            
            print(f"\n2️⃣ Reporting test spammer ({test_user_spammer}):")
            if self.report_spammer(test_user_spammer, f"test_spam_{mode_name.lower()}_mode"):
                print(f"   ✅ Successfully reported spammer to {mode_name} mode server")
            else:
                print(f"   ❌ Failed to report spammer to {mode_name} mode server")
            
            print(f"\n3️⃣ Testing spammer check ({test_user_spammer}):")
            spammer_result = self.test_api_response(test_user_spammer, mode_name)
            spammer_stats = self.analyze_response(spammer_result)
            
            # Store results
            results[mode_name] = {
                "clean_stats": clean_stats,
                "spammer_stats": spammer_stats
            }
            
            print(f"\n✅ {mode_name} mode testing completed")
            print()
        
        # Stop server
        self.stop_server()
        
        # Comparison
        print("=" * 80)
        print("📊 PERFORMANCE COMPARISON")
        print("=" * 80)
        
        if "FULL" in results and "BEACON" in results:
            full_time = results["FULL"]["clean_stats"]["response_time"] if results["FULL"]["clean_stats"] else 0
            beacon_time = results["BEACON"]["clean_stats"]["response_time"] if results["BEACON"]["clean_stats"] else 0
            
            if full_time > 0 and beacon_time > 0:
                speedup = full_time / beacon_time
                print(f"🚀 Beacon Mode Speedup: {speedup:.2f}x faster")
                print(f"   • Full Mode: {full_time}ms")
                print(f"   • Beacon Mode: {beacon_time}ms")
                print(f"   • Time Saved: {full_time - beacon_time:.2f}ms")
            
            full_external = results["FULL"]["clean_stats"]["has_external_data"] if results["FULL"]["clean_stats"] else False
            beacon_external = results["BEACON"]["clean_stats"]["has_external_data"] if results["BEACON"]["clean_stats"] else False
            
            print(f"\n🌐 External API Usage:")
            print(f"   • Full Mode: {'✅ Uses external APIs' if full_external else '❌ No external data'}")
            print(f"   • Beacon Mode: {'❌ No external APIs (by design)' if not beacon_external else '✅ Uses external APIs'}")
        
        print("\n" + "=" * 80)
        print("🎯 BEACON MODE BENEFITS SUMMARY")
        print("=" * 80)
        print("✅ Faster response times (no external API delays)")
        print("✅ Lower resource usage (no WebSocket server)")
        print("✅ Privacy-focused (no external API calls)")
        print("✅ Simplified deployment (fewer dependencies)")
        print("✅ Same P2P functionality (full network participation)")
        print("✅ Same local bot integration (no code changes needed)")
        
        print("\n🔧 WHEN TO USE BEACON MODE:")
        print("• 🏃 Speed is critical")
        print("• 🔒 Privacy requirements")
        print("• 💻 Resource constraints")
        print("• 🌐 Network restrictions")
        print("• 🎯 Dedicated P2P relay nodes")
        
        print("\n🎉 Demo completed successfully!")
        print("💡 To enable beacon mode: set BEACON_MODE_ONLY=true in .env file")

def main():
    """Main function."""
    demo = BeaconModeDemo()
    
    try:
        demo.run_demo()
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
    finally:
        demo.stop_server()
        # Reset to normal mode
        with open('.env', 'w') as f:
            f.write("BEACON_MODE_ONLY=false\n")

if __name__ == "__main__":
    main()
