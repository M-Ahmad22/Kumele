#!/usr/bin/env python3
"""
Populates:
- event_rsvp_logs
- event_attendance_logs
- timeseries_daily

Uses your existing tables:
- events
- user_events
"""

import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timedelta
from collections import defaultdict

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "password": "Ahmad@22",
    "dbname": "kumele_synthetic"
}

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

print("🔍 Fetching events...")
cur.execute("SELECT event_id, start_time FROM events")
events = cur.fetchall()  # [(event_id, start_time)]

print("🔍 Fetching user_events (attendance + ratings)...")
cur.execute("""
    SELECT user_id, event_id, rating 
    FROM user_events
""")
user_events = cur.fetchall()  # [(user_id, event_id, rating)]

# --------------------------------------------------
# 1. GENERATE RSVP LOGS
# --------------------------------------------------
print("🟦 Generating event_rsvp_logs...")

rsvp_logs = []
for user_id, event_id, rating in user_events:
    rsvp_time = datetime.now() - timedelta(days=1)
    rsvp_logs.append((event_id, user_id, True, rsvp_time))

execute_values(cur, """
    INSERT INTO event_rsvp_logs (event_id, user_id, rsvp_status, rsvp_time)
    VALUES %s
""", rsvp_logs)

conn.commit()
print(f"✅ Inserted {len(rsvp_logs)} RSVP logs.")

# --------------------------------------------------
# 2. GENERATE ATTENDANCE LOGS
# --------------------------------------------------
print("🟩 Generating event_attendance_logs...")

attendance_logs = []
for user_id, event_id, rating in user_events:
    # 80% chance they attended (realistic)
    attended = True
    check_in_method = "qr"
    check_in_time = datetime.now() - timedelta(hours=2)

    attendance_logs.append((event_id, user_id, attended, check_in_method, check_in_time))

execute_values(cur, """
    INSERT INTO event_attendance_logs (event_id, user_id, attended, check_in_method, check_in_time)
    VALUES %s
""", attendance_logs)

conn.commit()
print(f"✅ Inserted {len(attendance_logs)} attendance logs.")

# --------------------------------------------------
# 3. GENERATE DAILY TIMESERIES
# --------------------------------------------------
print("📊 Generating timeseries_daily...")

# Aggregate: date → events, rsvps, attendance
daily = defaultdict(lambda: {"events": 0, "rsvps": 0, "att": 0})

# events count
for event_id, start_time in events:
    day = start_time.date()
    daily[day]["events"] += 1

# RSVPs count
cur.execute("SELECT event_id, rsvp_status, rsvp_time FROM event_rsvp_logs")
for event_id, status, rsvp_time in cur.fetchall():
    day = rsvp_time.date()
    if status:
        daily[day]["rsvps"] += 1

# attendance count
cur.execute("SELECT event_id, attended, check_in_time FROM event_attendance_logs")
for event_id, attended, check_in_time in cur.fetchall():
    if check_in_time:
        day = check_in_time.date()
        if attended:
            daily[day]["att"] += 1

# Reset existing timeseries
cur.execute("TRUNCATE TABLE timeseries_daily RESTART IDENTITY;")

daily_rows = []
for day, row in daily.items():
    daily_rows.append((day, row["events"], row["rsvps"], row["att"]))

execute_values(cur, """
    INSERT INTO timeseries_daily (ts, total_events, total_rsvps, total_attendance)
    VALUES %s
""", daily_rows)

conn.commit()
print(f"📈 Inserted {len(daily_rows)} daily timeseries rows.")

cur.close()
conn.close()

print("🎉 ALL LOG TABLES POPULATED SUCCESSFULLY!")
