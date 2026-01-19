import os
import datetime
from . import mailer
from . import audit

# Paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
ALERTS_FILE = os.path.join(DATA_DIR, "alerts.csv")

# Memory cache for deduping (reset on restart is fine for now)
# Key: type+severity, Value: timestamp
recent_alerts = {} 

def log_alert(type: str, severity: str, message: str, context: str = ""):
    """
    Log alert to CSV and optionally Dispatch email.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    
    # 1. Dedupe (anti-spam)
    # If same alert type sent in last 60 mins -> skip email (but log event? maybe skip both to reduce noise)
    # Let's log all to CSV, but only email if not recently sent
    dedupe_key = f"{type}:{severity}"
    last_sent = recent_alerts.get(dedupe_key)
    
    should_email = True
    if last_sent:
        if (now - last_sent).total_seconds() < 3600: # 1 hour
            should_email = False
    
    # 2. Log to CSV
    try:
        with open(ALERTS_FILE, "a") as f:
            # timestamp,type,severity,message
            f.write(f"{now.isoformat()},{type},{severity},{message} - {context}\n")
    except:
        pass
        
    # 3. Email dispatch (High severity only or Test)
    if should_email and (severity in ["Warning", "Critical"] or type == "test"):
        subject = f"[SentinelMesh] {severity.upper()}: {type}"
        body = f"SentinelMesh Alert\n\nSeverity: {severity}\nType: {type}\n\nMessage: {message}\nContext: {context}\n\nTimestamp: {now.isoformat()}"
        
        mailer.send_email(subject, body)
        recent_alerts[dedupe_key] = now
        
        audit.log(f"Alert triggered: {type} ({severity})", "ALERT")
