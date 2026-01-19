import os
from fastapi.responses import FileResponse
from fastapi import HTTPException
from . import audit

# Paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

def get_file(resource: str):
    """
    Safely return a file for export.
    """
    valid_files = {
        "devices": "devices.json",
        "history": "history.csv",
        "alerts": "alerts.csv",
        "baseline": "baseline.json",
        "audit": "audit.log"
    }
    
    if resource not in valid_files:
        raise HTTPException(status_code=404, detail="Resource not found")
        
    filename = valid_files[resource]
    path = os.path.join(DATA_DIR, filename)
    
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"No data available for {resource} yet.")
        
    audit.log(f"Data exported: {resource}", "USER")
    return FileResponse(path, filename=filename, media_type='application/octet-stream')
