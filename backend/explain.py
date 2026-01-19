def explain_risk(risk_value: int) -> str:
    """
    Explains the risk score in plain English.
    """
    if risk_value == 0:
        return "System is stable. No active threats detected."
    elif risk_value < 50:
        return "Low risk. Minimal anomalies observed, but staying vigilant."
    else:
        return "Elevated risk. Unusual activity detected that requires attention."

def explain_status(state: str) -> str:
    """
    Explains the system status.
    """
    if state == "ok":
        return "All systems operational. Background monitors are active."
    return f"System is in {state} state."

def explain_missing_data(section_name: str) -> str:
    """
    Explains why data might be missing.
    """
    return f"No data for {section_name} yet. Specialized scanners have not been initialized."
