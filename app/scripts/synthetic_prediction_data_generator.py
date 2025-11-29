#!/usr/bin/env python3
"""
Kumele Synthetic Data Generator (Prediction Tables Only)

Populates:
 - users
 - events
 - event_rsvp_logs
 - event_attendance_logs
 - timeseries_daily

This version is CLEAN and built only for Prediction / ML training.
"""

import random
from faker import Faker
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timedelta
fake = Faker()
random.seed(42)

DB = {
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "password": "Ahmad@22",
    "dbname": "kumele_synthetic"
}

NUM_USERS = 250
NUM_EVENTS = 300

REAL_CITIES = [
    "New York", "London", "Berlin", "Paris", "Tokyo",
    "Toronto", "Sydney", "Dubai", "Singapore", "Nairobi"
]

REAL_HOBBIES = [
    "Music", "Sports", "Tech", "Art", "Food",
    "Travel", "Gaming", "Photography", "Cooking", "Fitness"
]

print("🔄 Connecting to DB...")
conn = psycopg2.connect(**DB)
cur = conn.cursor()

# ---------------------------------------------
# CLEAR OLD DATA + RESET SEQUENCES
# ---------------------------------------------
print("🧹 Clearing old tables...")

cur.execute("TRUNCATE TABLE event_attendance_logs CASCADE;")
cur.execute("TRUNCATE TABLE event_rsvp_logs CASCADE;")
cur.execute("TRUNCATE TABLE events CASCADE;")
cur.execute("TRUNCATE TABLE users CASCADE;")
cur.execute("TRUNCATE TABLE timeseries_daily CASCADE;")

# 🔥 Reset autoincrement sequences
cur.execute("ALTER SEQUENCE users_user_id_seq RESTART WITH 1;")
cur.execute("ALTER SEQUENCE events_event_id_seq RESTART WITH 1;")
cur.execute("ALTER SEQUENCE event_rsvp_logs_id_seq RESTART WITH 1;")
cur.execute("ALTER SEQUENCE event_attendance_logs_id_seq RESTART WITH 1;")

conn.commit()
print("✅ Tables + sequences reset")



# ---------------------------------------------
# USERS
# ---------------------------------------------
print("👤 Generating users...")

users = []
for _ in range(NUM_USERS):
    users.append((
        fake.name(),
        fake.unique.email(),
        fake.sha256(),
        random.randint(18, 60),
        random.choice(["Male", "Female"]),
        random.choice(REAL_CITIES),
        fake.country(),
        round(fake.latitude(), 5),
        round(fake.longitude(), 5),
        datetime.now() - timedelta(days=random.randint(5, 365)),
        datetime.now()
    ))

execute_values(cur, """
    INSERT INTO users 
    (full_name, email, password_hash, age, gender, city, country, latitude, longitude, created_at, last_login)
    VALUES %s
""", users)
conn.commit()

print("✅ Users done")


# ---------------------------------------------
# EVENTS
# ---------------------------------------------
print("📅 Generating events...")

events = []
start_base = datetime.now() - timedelta(days=365)

for _ in range(NUM_EVENTS):
    start = start_base + timedelta(days=random.randint(1, 300))
    end = start + timedelta(hours=random.randint(1, 4))

    events.append((
        fake.sentence(nb_words=4),
        random.choice(REAL_HOBBIES),
        random.choice(REAL_CITIES),
        fake.country(),
        round(fake.latitude(), 5),
        round(fake.longitude(), 5),
        start,
        end,
        random.randint(1, NUM_USERS)
    ))

execute_values(cur, """
    INSERT INTO events
    (event_name, category, city, country, latitude, longitude, start_time, end_time, organiser_id)
    VALUES %s
""", events)
conn.commit()

print("✅ Events generated")


# ---------------------------------------------
# RSVPs + Attendance
# ---------------------------------------------
print("🟢 Generating RSVPs & Attendance...")

cur.execute("SELECT event_id, start_time FROM events")
event_rows = cur.fetchall()

rsvp_logs = []
att_logs = []

for event_id, start_time in event_rows:
    # random RSVP count
    rsvp_count = random.randint(20, 150)
    attending = int(rsvp_count * random.uniform(0.4, 0.9))

    attending_users = random.sample(range(1, NUM_USERS), attending)

    # RSVPs
    for _ in range(rsvp_count):
        uid = random.randint(1, NUM_USERS)
        rsvp_logs.append((event_id, uid, True, start_time - timedelta(days=random.randint(1, 15))))

    # Attendance logs
    for uid in attending_users:
        att_logs.append((
            event_id,
            uid,
            True,
            random.choice(["qr", "geo", "manual"]),
            start_time + timedelta(minutes=random.randint(1, 30))
        ))

execute_values(cur, """
    INSERT INTO event_rsvp_logs
    (event_id, user_id, rsvp_status, rsvp_time)
    VALUES %s
""", rsvp_logs)

execute_values(cur, """
    INSERT INTO event_attendance_logs
    (event_id, user_id, attended, check_in_method, check_in_time)
    VALUES %s
""", att_logs)

conn.commit()
print("✅ RSVP & Attendance done")


# ---------------------------------------------
# BUILD DAILY TIMESERIES
# ---------------------------------------------
print("📊 Building timeseries_daily...")

cur.execute("""
    INSERT INTO timeseries_daily (ts, total_events, total_rsvps, total_attendance)
    SELECT 
        day,
        COUNT(*) AS total_events,
        SUM(rsvp_yes) AS total_rsvps,
        SUM(att_yes) AS total_attendance
    FROM (
        SELECT
            DATE(e.start_time) AS day,
            (
                SELECT COUNT(*) 
                FROM event_rsvp_logs r
                WHERE r.event_id = e.event_id
            ) AS rsvp_yes,
            (
                SELECT COUNT(*) 
                FROM event_attendance_logs a
                WHERE a.event_id = e.event_id
            ) AS att_yes
        FROM events e
    ) AS sub
    GROUP BY day
    ORDER BY day;
""")
conn.commit()

print("✅ timeseries_daily populated")

print("🎉 Synthetic Prediction Dataset Ready!")

cur.close()
conn.close()
