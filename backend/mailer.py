import os
import json
import smtplib
from email.mime.text import MIMEText
from . import audit

# Paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
ENV_FILE = os.path.join(DATA_DIR, "environment.json")

def load_config():
    """Load email config."""
    try:
        with open(ENV_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def send_email(subject, body):
    """
    Send email safely.
    Never crash. Logs result.
    """
    config = load_config()
    
    if not config.get("email_enabled"):
        return # Email disabled
        
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = config.get("sender_email")
        msg['To'] = config.get("recipient_email")
        
        server = smtplib.SMTP(config.get("smtp_server"), config.get("smtp_port"))
        server.starttls()
        server.login(config.get("sender_email"), config.get("sender_password"))
        server.send_message(msg)
        server.quit()
        
        audit.log(f"Email sent: {subject}", "MAILER")
        return True
        
    except Exception as e:
        audit.log(f"Email failure: {str(e)}", "ERROR")
        return False
