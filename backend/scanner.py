import os
import json
import subprocess
import re
import datetime
from . import audit
import psutil

# Paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DEVICES_FILE = os.path.join(DATA_DIR, "devices.json")

def load_devices():
    """Load existing devices from JSON."""
    if not os.path.exists(DEVICES_FILE):
        return []
    try:
        with open(DEVICES_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_devices(devices):
    """Save devices to JSON."""
    try:
        with open(DEVICES_FILE, "w") as f:
            json.dump(devices, f, indent=2)
    except Exception as e:
        audit.log(f"Failed to save devices: {str(e)}", "ERROR")

def get_arp_table():
    """
    Get ARP table from OS (passive discovery).
    Returns list of dicts: {'ip': str, 'mac': str}
    """
    devices = []
    try:
        # Run arp -a
        output = subprocess.check_output("arp -a", shell=True).decode("utf-8", errors="ignore")
        
        # Regex for IP and MAC (Windows format)
        # Interface: 192.168.1.5 --- 0x10
        #   Internet Address      Physical Address      Type
        #   192.168.1.1           ab-cd-ef-12-34-56     dynamic
        
        # Pattern to capture IP and MAC
        pattern = re.compile(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+([a-fA-F0-9-]{17})\s+")
        
        for line in output.splitlines():
            match = pattern.search(line)
            if match:
                ip = match.group(1)
                mac = match.group(2).replace("-", ":").upper()
                # Filter out multicast/broadcast
                if ip.startswith("224.") or ip.startswith("239.") or ip == "255.255.255.255":
                    continue
                devices.append({"ip": ip, "mac": mac})
                
    except Exception as e:
        audit.log(f"ARP scan failed: {str(e)}", "ERROR")
        
    return devices

def get_last_scan_time():
    """Return the timestamp of the last scan or 'never'."""
    # We'll infer this from the audit log or metadata in future.
    # For now, just return a simple state or check file mod time.
    if os.path.exists(DEVICES_FILE):
        try:
            mtime = os.path.getmtime(DEVICES_FILE)
            dt = datetime.datetime.fromtimestamp(mtime, datetime.timezone.utc)
            return dt.isoformat()
        except:
            pass
    return "never"

def scan_devices():
    """
    Main scan logic.
    1. Load existing devices.
    2. Get current ARP table.
    3. Merge and update timestamps.
    4. Save.
    5. Return full list.
    """
    audit.log("Device scan started", "SCANNER")
    
    known = {d["ip"]: d for d in load_devices()}
    current = get_arp_table()
    
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    # Process found devices
    for d in current:
        ip = d["ip"]
        mac = d["mac"]
        
        if ip in known:
            known[ip]["last_seen"] = now
            known[ip]["mac"] = mac # Update MAC if changed (rare)
            known[ip]["status"] = "active"
        else:
            known[ip] = {
                "ip": ip,
                "mac": mac,
                "first_seen": now,
                "last_seen": now,
                "status": "active"
            }
            
    # Update status for devices NOT seen
    # If not seen in 5 mins -> active (tolerance)
    # If not seen in 24 hours -> idle
    # If not seen in 7 days -> archived
    
    found_ips = set(d["ip"] for d in current)
    result_list = []
    
    for ip, device in known.items():
        if ip not in found_ips:
            # Check how long since last_seen
            try:
                last = datetime.datetime.fromisoformat(device["last_seen"])
                delta = datetime.datetime.now(datetime.timezone.utc) - last
                
                if delta.total_seconds() > 7 * 86400: # 7 days
                    device["status"] = "archived"
                elif delta.total_seconds() > 86400: # 24 hours
                    device["status"] = "idle"
                else:
                    # Keep as active for a bit of tolerance, strictly if not in scan it might be just quiet
                    # But prompt says "Active = seen in last 5 min".
                    if delta.total_seconds() > 300: # 5 mins
                         if device["status"] == "active":
                             device["status"] = "idle" # Fallback to idle if > 5 mins
            except:
                pass
        
        result_list.append(device)
        
    save_devices(result_list)
    audit.log(f"Device scan complete. Found {len(current)} active devices.", "SCANNER")
    return result_list
