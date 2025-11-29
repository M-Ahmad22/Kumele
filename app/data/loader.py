# """
# Data loader utilities:
# - read CSV synthetic files into pandas DataFrames
# - lightweight DB helpers (placeholder) to fetch user/event rows
# """

# import pandas as pd
# import os
# from typing import Dict, Any

# BASE = os.path.dirname(__file__)

# def load_users_csv(path=None):
#     p = path or os.path.join(BASE, "..", "data", "users.csv")
#     if not os.path.exists(p):
#         # return empty df
#         return pd.DataFrame()
#     return pd.read_csv(p)

# def load_events_csv(path=None):
#     p = path or os.path.join(BASE, "..", "data", "events.csv")
#     if not os.path.exists(p):
#         return pd.DataFrame()
#     return pd.read_csv(p)

# # In production: replace with DB queries (psycopg2 / SQLAlchemy)
# def build_inmemory_user_db(users_df):
#     d = {}
#     for _, r in users_df.iterrows():
#         uid = int(r["user_id"])
#         d[uid] = {
#             "name": r.get("name", f"user_{uid}"),
#             "hobbies": (r.get("hobbies") or "").split("|") if r.get("hobbies") else [],
#             "lat": float(r.get("lat", 0.0)) if r.get("lat") else 0.0,
#             "lon": float(r.get("lon", 0.0)) if r.get("lon") else 0.0,
#             "age": int(r.get("age", 0)),
#             "reward_status": r.get("reward_status", None),
#             "gold_count": int(r.get("gold_count", 0))
#         }
#     return d

# def build_inmemory_event_db(events_df):
#     d = {}
#     for _, r in events_df.iterrows():
#         eid = int(r["event_id"])
#         d[eid] = {
#             "title": r.get("title", ""),
#             "hobby": r.get("hobby", ""),
#             "lat": float(r.get("lat", 0.0)) if r.get("lat") else 0.0,
#             "lon": float(r.get("lon", 0.0)) if r.get("lon") else 0.0,
#             # event embedding will be filled by model loader in production
#             "embedding": None
#         }
#     return d


# app/data/loader.py
from sqlalchemy.orm import Session
from app.db.database import get_real_db
from app.db.models import User

def fetch_all_users(db: Session):
    return db.query(User).limit(100).all()


def load_users_csv(file_path):
    """Load users from a CSV file"""
    users = []
    try:
        with open(file_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                users.append(row)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    return users

def load_events_csv(file_path):
    """Load events from a CSV file"""
    events = []
    try:
        with open(file_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                events.append(row)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    return events

# ------------------------
# In-memory DB builders
# ------------------------
def build_inmemory_user_db(users_list):
    """Convert list of user dicts into a dict keyed by user_id"""
    return {user['id']: user for user in users_list}

def build_inmemory_event_db(events_list):
    """Convert list of event dicts into a dict keyed by event_id"""
    return {event['id']: event for event in events_list}