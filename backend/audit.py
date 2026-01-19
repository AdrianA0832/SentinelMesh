import os
import datetime

# Define path relative to this file
LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "audit.log")

def log(event: str, level: str = "INFO"):
    """
    Append-only, crash-safe logging to a local file.
    """
    try:
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        entry = f"[{timestamp}] [{level}] {event}\n"
        
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
            
    except Exception:
        # ABSOLUTE RULE: Never crash the application because logging failed
        pass
