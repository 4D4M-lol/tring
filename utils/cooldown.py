from datetime import datetime, timedelta

COOLDOWN_DAYS = {
    "username": 30,
    "password": 7
}

def check_cooldown(last_change_time, feature_name):
    if not last_change_time:
        return True, 0

    allowed_days = COOLDOWN_DAYS.get(feature_name, 0)
    next_allowed_date = last_change_time + timedelta(days=allowed_days)
    now = datetime.utcnow()

    if now >= next_allowed_date:
        return True, 0
    else:
        remaining = (next_allowed_date - now).days + 1
        
        return False, remaining