import os
import datetime
import psutil
from . import audit
from . import baseline
from . import explain

# Paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
HISTORY_FILE = os.path.join(DATA_DIR, "history.csv")

def get_metrics():
    """
    Collect active connection metrics from OS.
    Metadata only. No packet capture.
    """
    counts = {
        "total": 0,
        "dns": 0
    }
    try:
        # Get connections (metadata only)
        connections = psutil.net_connections(kind='inet')
        counts["total"] = len(connections)
        
        # Count DNS (port 53)
        for c in connections:
            if c.raddr and (c.raddr.port == 53):
                counts["dns"] += 1
                
    except Exception as e:
        audit.log(f"Metrics collection failed: {str(e)}", "ERROR")
        
    return counts

def analyze():
    """
    Analyze current metrics against baseline.
    Returns dict with risk score and explanations.
    """
    metrics = get_metrics()
    base_data = baseline.load_baseline()
    
    score = 0
    anomalies = []
    
    # 1. Baseline Comparison (if active)
    if base_data.get("status") == "active" or (not base_data.get("learning_mode") and base_data.get("created_at")):
        learned = base_data.get("learned_metrics", {})
        avg_conns = learned.get("connection_count_avg", 0)
        
        if avg_conns > 0:
            # Anomaly: Total connections > 2x baseline
            if metrics["total"] > (avg_conns * 2) and metrics["total"] > 10: # Threshold of 10 to ignore noise
                score += 30
                anomalies.append(f"Connection spike detected ({metrics['total']} > {int(avg_conns * 2)})")
                
            # Anomaly: DNS burst (heuristic: > 20 concurrent DNS connections is suspicious for a home network)
            if metrics["dns"] > 20: 
                score += 50
                anomalies.append(f"High DNS traffic burst ({metrics['dns']} active queries)")
    
    # Cap score
    score = min(score, 100)
    
    # Generate Explanation
    if score == 0:
        if base_data.get("learning_mode"):
            reason = "System is learning normal behavior."
        else:
            reason = explain.explain_risk(0)
    else:
        reason = f"Elevated Risk: {'; '.join(anomalies)}"
        
    # Log to history
    log_history(metrics, score, len(anomalies))
    
    # Audit if risk is high
    if score >= 50:
        audit.log(f"High risk detected: {score}. {reason}", "RISK")
        
    return {
        "score": score,
        "status": "Normal" if score < 50 else "Warning" if score < 80 else "Critical",
        "explanation": reason,
        "metrics": metrics
    }

def log_history(metrics, score, anomaly_count):
    """Append to CSV history."""
    try:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        line = f"{now},{metrics['total']},{metrics['dns']},{score},{anomaly_count}\n"
        with open(HISTORY_FILE, "a") as f:
            f.write(line)
    except:
        pass
