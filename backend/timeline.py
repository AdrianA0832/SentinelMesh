import os
import csv
import re
from . import audit

# Paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
AUDIT_FILE = os.path.join(DATA_DIR, "audit.log")
ALERTS_FILE = os.path.join(DATA_DIR, "alerts.csv")
HISTORY_FILE = os.path.join(DATA_DIR, "history.csv")

def get_events(limit: int = 100, source_filter: str = None):
    """
    Aggregate events from multiple sources into a single timeline.
    Normalized format:
    {
        "timestamp": ISO string,
        "source": "audit" | "alert" | "analyzer",
        "level": "INFO" | "WARNING" | "CRITICAL" | etc,
        "message": string
    }
    """
    events = []
    
    # 1. Parse Audit Log
    # Format: [ISO] [LEVEL] Message
    if os.path.exists(AUDIT_FILE):
        try:
            with open(AUDIT_FILE, "r", encoding="utf-8") as f:
                pattern = re.compile(r"^\[(.*?)\] \[(.*?)\] (.*)$")
                for line in f:
                    match = pattern.match(line.strip())
                    if match:
                        events.append({
                            "timestamp": match.group(1),
                            "source": "audit",
                            "level": match.group(2),
                            "message": match.group(3)
                        })
        except:
            pass

    # 2. Parse Alerts CSV
    # Format: timestamp,type,severity,message
    if os.path.exists(ALERTS_FILE):
        try:
            with open(ALERTS_FILE, "r") as f:
                reader = csv.reader(f)
                header = next(reader, None) # Skip header
                for row in reader:
                    if len(row) >= 4:
                        events.append({
                            "timestamp": row[0],
                            "source": "alert",
                            "level": row[2], # severity
                            "message": f"{row[1]}: {row[3]}" # type: message
                        })
        except:
            pass

    # 3. Parse History CSV (Risk > 50 only)
    # Format: timestamp,total,dns,risk,anomalies
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                for row in reader:
                    if len(row) >= 5:
                        risk_score = float(row[3])
                        if risk_score >= 50:
                            events.append({
                                "timestamp": row[0],
                                "source": "analyzer",
                                "level": "High Risk",
                                "message": f"Risk Score {row[3]} - {row[4]} anomalies"
                            })
        except:
            pass
            
    # Filter
    if source_filter:
        events = [e for e in events if e["source"] == source_filter]
        
    # Sort by timestamp descending (newest first)
    # Simple string sort works for ISO8601
    events.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return events[:limit]
