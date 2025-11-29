"""
Quick synthetic data generator for local experiments.
Produces users.csv, events.csv, interactions.csv in the local app/data/ folder.
Fields align with the project spec used for training first models.
"""

import csv
import os
import random
from faker import Faker

BASE = os.path.dirname(__file__)
OUTDIR = os.path.join(BASE, "..", "data")
os.makedirs(OUTDIR, exist_ok=True)

fake = Faker()

HOBBIES = ["Photography", "Hiking", "Board Games", "Chess", "Gardening", "Cooking", "Running"]

def gen_users(n=200):
    path = os.path.join(OUTDIR, "users.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["user_id","name","age","lat","lon","hobbies","reward_status","gold_count"])
        for uid in range(1000, 1000+n):
            name = fake.name()
            age = random.randint(16, 60)
            lat = round(51.3 + random.random()*0.4, 6)
            lon = round(-0.2 + random.random()*0.4, 6)
            hobbies = "|".join(random.sample(HOBBIES, random.randint(1,3)))
            reward_status = random.choice(["Gold", "Silver", "Bronze", None])
            gold_count = random.randint(0, 5)
            writer.writerow([uid, name, age, lat, lon, hobbies, reward_status, gold_count])
    print("Users saved:", path)

def gen_events(n=40):
    path = os.path.join(OUTDIR, "events.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["event_id","title","hobby","lat","lon"])
        for eid in range(2000, 2000+n):
            hobby = random.choice(HOBBIES)
            title = f"{hobby} Meetup {random.randint(1,100)}"
            lat = round(51.3 + random.random()*0.4, 6)
            lon = round(-0.2 + random.random()*0.4, 6)
            writer.writerow([eid, title, hobby, lat, lon])
    print("Events saved:", path)

def gen_interactions(n=2000, users_n=200, events_n=40):
    # interactions.csv: user_id,event_id,timestamp,action (view|join|like)
    path = os.path.join(OUTDIR, "interactions.csv")
    user_ids = [1000+i for i in range(users_n)]
    event_ids = [2000+i for i in range(events_n)]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["user_id","event_id","timestamp","action"])
        for i in range(n):
            uid = random.choice(user_ids)
            eid = random.choice(event_ids)
            ts = fake.date_time_between(start_date='-180d', end_date='now').isoformat()
            action = random.choices(["view","join","like"], weights=[0.7,0.2,0.1])[0]
            writer.writerow([uid, eid, ts, action])
    print("Interactions saved:", path)

if __name__ == "__main__":
    gen_users(300)
    gen_events(80)
    gen_interactions(3000, users_n=300, events_n=80)
