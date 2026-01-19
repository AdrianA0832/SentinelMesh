from fastapi import FastAPI, Body
from datetime import datetime
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend import audit
from backend import baseline
from backend import analyzer
from backend import alerts
from backend import timeline
from backend import exporter
from backend import health
from backend import scanner
from backend import explain

# Global State
READ_ONLY = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global READ_ONLY
    if health.check_storage() != "ok":
        READ_ONLY = True
        audit.log("System startup (READ-ONLY MODE)", "SYSTEM")
    else:
        audit.log("System startup", "SYSTEM")
    yield
    # Shutdown
    audit.log("System shutdown", "SYSTEM")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/status")
def status():
    return {
        "ok": True,
        "service": "sentinelmesh",
        "time": datetime.utcnow().isoformat()
    }

@app.get("/")
def health_check():
    status = "ok"
    risk_analysis = analyzer.analyze()
    
    # Trigger Alert if Risk is High
    if risk_analysis["score"] >= 50 and not READ_ONLY: # Don't spam alerts if broken
        severity = "Critical" if risk_analysis["score"] >= 80 else "Warning"
        alerts.log_alert("High Risk", severity, risk_analysis["explanation"], f"Score: {risk_analysis['score']}")

    explanations = {
        "risk": risk_analysis["explanation"],
        "data": explain.explain_missing_data("network_map"),
        "state": explain.explain_status(status)
    }
    
    audit.log("Health check with explanations generated")
    
    system_mode = "read-only" if READ_ONLY else "read-write"
    
    return {
        "status": status,
        "mode": system_mode,
        "risk_score": risk_analysis["score"],
        "risk_status": risk_analysis["status"],
        "explanations": explanations
    }

@app.post("/alerts/test")
def test_alert():
    if READ_ONLY:
         return {"status": "Failed. System is Read-Only."}
    alerts.log_alert("test", "Info", "Manual test requested", "User triggered")
    return {"status": "Test alert dispatched"}

@app.get("/timeline")
def get_timeline(source: str = None):
    audit.log(f"Timeline accessed (filter: {source})", "USER")
    return timeline.get_events(source_filter=source)

@app.get("/export/{resource}")
def export_data(resource: str):
    return exporter.get_file(resource)

@app.get("/health")
def self_check():
    audit.log("Health self-check initiated")
    return {
        "storage": health.check_storage(),
        "audit": health.check_audit_log(),
        "baseline": health.check_baseline(),
        "scanner": "inactive",
        "last_scan": health.last_scan_time()
    }

@app.get("/devices")
def get_devices():
    devices = scanner.scan_devices()
    baseline.update(devices)
    return list(devices)

@app.get("/environment")
def get_env():
    return baseline.get_environment_info()

class EnvNameRequest(BaseModel):
    name: str

@app.post("/environment/name")
def set_env_name(req: EnvNameRequest):
    success = baseline.set_environment_name(req.name)
    return {"success": success, "name": req.name}
