#!/usr/bin/env python3
"""
Show nodes that are trying to connect to help with whitelisting decisions
"""

import re
import os
from datetime import datetime, timedelta
import json

def parse_security_log():
    """Parse security.log to show recent connection attempts"""
    log_file = "security.log"
    
    if not os.path.exists(log_file):
        print("📋 No security.log file found")
        print("💡 Start the server to begin logging connection attempts")
        return
    
    print("🔍 Recent P2P Connection Attempts (last 24 hours):")
    print("=" * 60)
    
    # Parse recent entries
    cutoff_time = datetime.now() - timedelta(hours=24)
    connections = []
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                # Look for various connection-related events
                if any(keyword in line for keyword in [
                    "CONNECTION_REJECTED", "CONNECTION_ACCEPTED", "HANDSHAKE", 
                    "AUTHENTICATION", "P2P connection", "connectionMade"
                ]):
                    # Extract timestamp
                    match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                    if match:
                        timestamp_str = match.group(1)
                        try:
                            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                            if timestamp > cutoff_time:
                                connections.append((timestamp, line.strip()))
                        except ValueError:
                            continue
    except FileNotFoundError:
        print("📋 No security.log file found")
        return
    except Exception as e:
        print(f"❌ Error reading log file: {e}")
        return
    
    if not connections:
        print("📋 No recent connection attempts found")
        print("💡 Make sure the server is running and P2P connections are being attempted")
        return
    
    # Sort by timestamp and show recent entries
    connections.sort(key=lambda x: x[0])
    
    # Group by IP and node for better analysis
    connection_summary = {}
    
    for timestamp, log_line in connections[-50:]:  # Analyze last 50 entries
        # Extract IP
        ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', log_line)
        ip = ip_match.group(1) if ip_match else "unknown"
        
        # Extract node UUID if present
        node_match = re.search(r'UUID[:\s]+([a-fA-F0-9-]+)', log_line)
        node_uuid = node_match.group(1) if node_match else "unknown"
        
        # Determine connection status
        if any(rejected in log_line.upper() for rejected in ["REJECTED", "FAILED", "BLOCKED", "DENIED"]):
            status = "REJECTED"
        elif any(accepted in log_line.upper() for accepted in ["ACCEPTED", "SUCCESS", "COMPLETED", "MADE"]):
            status = "ACCEPTED"
        else:
            status = "UNKNOWN"
        
        # Group by IP
        if ip not in connection_summary:
            connection_summary[ip] = {"attempts": [], "nodes": set(), "last_seen": timestamp}
        
        connection_summary[ip]["attempts"].append((timestamp, status, node_uuid))
        if node_uuid != "unknown":
            connection_summary[ip]["nodes"].add(node_uuid)
        connection_summary[ip]["last_seen"] = max(connection_summary[ip]["last_seen"], timestamp)
    
    # Display summary
    print("\n📊 Connection Summary by IP Address:")
    for ip, data in sorted(connection_summary.items(), key=lambda x: x[1]["last_seen"], reverse=True):
        attempts = data["attempts"]
        nodes = data["nodes"]
        
        accepted_count = sum(1 for _, status, _ in attempts if status == "ACCEPTED")
        rejected_count = sum(1 for _, status, _ in attempts if status == "REJECTED")
        
        print(f"\n🌐 IP: {ip}")
        print(f"   📊 Attempts: {len(attempts)} (✅ {accepted_count} accepted, ❌ {rejected_count} rejected)")
        print(f"   🕐 Last seen: {data['last_seen'].strftime('%H:%M:%S')}")
        
        if nodes and "unknown" not in nodes:
            print(f"   🏷️  Node UUIDs:")
            for node in sorted(nodes):
                print(f"      • {node}")
        elif len(attempts) > 0:
            print("   ⚠️  No node UUID detected in logs")
    
    # Show recent individual attempts
    print(f"\n🕐 Last 10 Connection Attempts:")
    for timestamp, log_line in connections[-10:]:
        ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', log_line)
        ip = ip_match.group(1) if ip_match else "unknown"
        
        time_str = timestamp.strftime('%H:%M:%S')
        
        if any(rejected in log_line.upper() for rejected in ["REJECTED", "FAILED", "BLOCKED"]):
            print(f"   🕐 {time_str} | 🌐 {ip:<15} | ❌ REJECTED")
        elif any(accepted in log_line.upper() for accepted in ["ACCEPTED", "SUCCESS", "COMPLETED"]):
            print(f"   🕐 {time_str} | 🌐 {ip:<15} | ✅ ACCEPTED")
        else:
            print(f"   🕐 {time_str} | 🌐 {ip:<15} | ❓ UNKNOWN")

def show_current_whitelist():
    """Show current whitelist status"""
    print("\n🔐 Current Whitelist Configuration:")
    print("-" * 40)
    
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Extract allowed nodes
        allowed_match = re.search(r'ALLOWED_NODE_KEYS=(.+)', content)
        if allowed_match:
            allowed_nodes = allowed_match.group(1).strip()
            if allowed_nodes:
                nodes = [n.strip() for n in allowed_nodes.split(',') if n.strip()]
                print(f"✅ Whitelist ACTIVE: {len(nodes)} trusted nodes")
                for i, node in enumerate(nodes, 1):
                    print(f"   {i}. {node}")
            else:
                print("🔓 Whitelist DISABLED: All nodes allowed")
        else:
            print("🔓 Whitelist DISABLED: No ALLOWED_NODE_KEYS configured")
    else:
        print("❌ No .env file found")

def suggest_whitelist_actions():
    """Suggest actions based on connection attempts"""
    print("\n💡 Whitelist Management Suggestions:")
    print("-" * 40)
    
    print("🔧 To add a trusted node:")
    print("   python manage_trusted_nodes.py add <node-uuid-or-key>")
    
    print("\n🔧 To view current whitelist:")
    print("   python manage_trusted_nodes.py list")
    
    print("\n🔧 To check full security status:")
    print("   python configure_security.py status")
    
    print("\n📝 Notes:")
    print("   • Look for repeated connection attempts from the same IP")
    print("   • Check if node UUIDs are visible in the logs")
    print("   • Trusted nodes should have consistent UUIDs")
    print("   • Restart server after whitelist changes")

def main():
    print("🔍 P2P Connection Monitor & Whitelist Helper")
    print("=" * 50)
    
    try:
        parse_security_log()
        show_current_whitelist()
        suggest_whitelist_actions()
        
    except KeyboardInterrupt:
        print("\n❌ Monitoring interrupted")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
