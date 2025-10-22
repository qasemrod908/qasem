from datetime import datetime, timedelta

def damascus_now():
    return datetime.utcnow() + timedelta(hours=3)
