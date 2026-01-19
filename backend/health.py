import os

# Define path relative to this file
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
LOG_FILE = os.path.join(DATA_DIR, "audit.log")

def check_storage() -> str:
    """Checks if data directory is writable."""
    try:
        if not os.path.exists(DATA_DIR):
            return "error"
        # Try writing a temp file
        test_file = os.path.join(DATA_DIR, ".health_test")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        return "ok"
    except Exception:
        return "readonly"

def check_audit_log() -> str:
    """Checks if audit log exists."""
    try:
        if os.path.exists(LOG_FILE):
            return "ok"
        return "missing"
    except Exception:
        return "error"

from backend import scanner
from backend import baseline

def check_baseline() -> str:
    """Returns baseline status."""
    return baseline.get_status()

def last_scan_time() -> str:
    """Returns timestamp of last scan."""
    return scanner.get_last_scan_time()
