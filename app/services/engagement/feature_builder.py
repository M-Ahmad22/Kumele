from datetime import datetime

def build_user_features(user, last_event, reward_status, messages_30):
    days_since_login = (datetime.now() - user.last_login).days
    days_since_event = (datetime.now() - last_event).days if last_event else 999

    return {
        "days_since_login": days_since_login,
        "days_since_event": days_since_event,
        "messages_30": messages_30,
        "reward_status": reward_status,
    }
