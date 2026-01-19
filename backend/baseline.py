import os
import json
import datetime
import subprocess
import re
from . import audit

# Paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
BASELINE_FILE = os.path.join(DATA_DIR, "baseline.json")

def get_environment_fingerprint():
    """
    Generate a simple fingerprint for the current network environment.
    Uses the default gateway IP (e.g. router IP) as a proxy for 'Location'.
    """
    try:
        # Simple extraction of default gateway (Windows)
        output = subprocess.check_output("ipconfig", shell=True).decode("utf-8", errors="ignore")
        # Look for Default Gateway . . . . . . . . . : 192.168.1.1
        match = re.search(r"Default Gateway.*: (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", output)
        if match:
            return match.group(1)
    except:
        pass
    return "unknown_env"

def load_baseline():
    """Load baseline from JSON."""
    if not os.path.exists(BASELINE_FILE):
        return {}
    try:
        with open(BASELINE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_baseline(data):
    """Save baseline to JSON."""
    try:
        with open(BASELINE_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        audit.log(f"Failed to save baseline: {str(e)}", "ERROR")

def reset_baseline(fingerprint, reason):
    """Archive old baseline and start new one."""
    audit.log(f"Baseline reset. Reason: {reason}", "BASELINE")
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    new_baseline = {
        "environment_id": fingerprint,
        "environment_name": None,
        "created_at": now,
        "learning_mode": True,
        "learned_metrics": {
            "device_count_avg": 0,
            "sample_count": 0
        },
        "samples": []
    }
    save_baseline(new_baseline)
    return new_baseline

def update(current_devices):
    """
    Update baseline with current scan results.
    Handles environment changes and learning mode.
    """
    fingerprint = get_environment_fingerprint()
    baseline = load_baseline()
    
    # 1. Check environment
    if baseline.get("environment_id") != fingerprint:
        baseline = reset_baseline(fingerprint, "Environment changed")
        
    if not baseline.get("learning_mode"):
        return # Already learned, just holding steady
        
    # 2. Check time (10 mins learning)
    created = datetime.datetime.fromisoformat(baseline["created_at"])
    now = datetime.datetime.now(datetime.timezone.utc)
    age = (now - created).total_seconds()
    
    if age > 600: # 10 mins
        baseline["learning_mode"] = False
        audit.log("Baseline learning finished. Mode set to ACTIVE.", "BASELINE")
        save_baseline(baseline)
        return

    # 3. Learn
    # We track average active device count AND connection counts
    active_count = len([d for d in current_devices if d.get("status") == "active"])
    
    # Get current connections (lightweight check just for learning)
    try:
        import psutil
        conn_count = len(psutil.net_connections(kind='inet'))
    except:
        conn_count = 0

    metrics = baseline["learned_metrics"]
    count = metrics["sample_count"]
    
    # Device avg
    dev_avg = metrics.get("device_count_avg", 0)
    new_dev_avg = ((dev_avg * count) + active_count) / (count + 1)
    metrics["device_count_avg"] = new_dev_avg
    
    # Connection avg
    conn_avg = metrics.get("connection_count_avg", 0)
    new_conn_avg = ((conn_avg * count) + conn_count) / (count + 1)
    metrics["connection_count_avg"] = new_conn_avg
    
    metrics["sample_count"] = count + 1
    
    save_baseline(baseline)

def get_status():
    """Return status string for health check."""
    baseline = load_baseline()
    if not baseline:
        return "inactive"
    if baseline.get("learning_mode"):
        return "learning"
    return "active"

def get_environment_info():
    """Get current environment details."""
    baseline = load_baseline()
    env_id = baseline.get("environment_id", "unknown")
    name = baseline.get("environment_name")
    
    # Needs name if we have an ID but no name
    needs_name = (env_id != "unknown" and not name)
    
    return {
        "environment_id": env_id,
        "name": name,
        "needs_name": needs_name
    }

def set_environment_name(name):
    """Set simple label for current environment."""
    baseline = load_baseline()
    if not baseline:
         return False
         
    old_name = baseline.get("environment_name")
    baseline["environment_name"] = name
    save_baseline(baseline)
    
    audit.log(f"Environment named: '{name}' (was: {old_name})", "USER")
    return True
