#!/usr/bin/env python3
"""
Extended Kumele synthetic data generator:
Generates users, hobbies, events, blogs, ads, and all interactions
Fully compatible with PostgreSQL
"""

import random
from faker import Faker
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timedelta

fake = Faker()
random.seed(42)

NUM_USERS = 500
NUM_HOBBIES = 10
NUM_EVENTS = 200
NUM_BLOGS = 300
NUM_ADS = 100

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "password": "Ahmad@22",
    "dbname": "kumele_synthetic"    
}

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

tables_to_clear = ["ad_interactions","ads","blog_interactions","blogs",
                   "user_events","user_hobbies","events","users","referrals"]

for table in tables_to_clear:
    cur.execute(f"TRUNCATE TABLE {table} CASCADE;")
conn.commit()
print("✅ All tables cleared")

# --------------------------
# USERS
# --------------------------
users = []
for _ in range(NUM_USERS):
    users.append((
        fake.name(),
        fake.unique.email(),
        fake.sha256(),
        random.randint(18, 60),
        random.choice(["Male", "Female", "Other"]),
        fake.city(),
        fake.country(),
        round(fake.latitude(),6),
        round(fake.longitude(),6),
        datetime.now() - timedelta(days=random.randint(0,365)),  # created_at
        datetime.now() - timedelta(days=random.randint(0,30))    # last_login
    ))

execute_values(cur,
    """INSERT INTO users 
    (full_name,email,password_hash,age,gender,city,country,latitude,longitude,created_at,last_login)
    VALUES %s""",
    users
)
conn.commit()
print("✅ Users generated")

# --------------------------
# HOBBIES
# --------------------------
hobbies_list = ["Music","Sports","Tech","Art","Food","Travel","Gaming","Photography","Cooking","Reading"]
hobbies = [(h, "General") for h in hobbies_list]
execute_values(cur,
    "INSERT INTO hobbies (hobby_name, category) VALUES %s",
    hobbies
)
conn.commit()
print("✅ Hobbies generated")

# --------------------------
# USER-HOBBIES
# --------------------------
cur.execute("SELECT user_id FROM users")
user_ids = [row[0] for row in cur.fetchall()]
cur.execute("SELECT hobby_id FROM hobbies")
hobby_ids = [row[0] for row in cur.fetchall()]

user_hobbies = []
for uid in user_ids:
    selected = random.sample(hobby_ids, k=random.randint(1,3))
    for hid in selected:
        user_hobbies.append((uid,hid,random.randint(1,5)))

execute_values(cur,
    "INSERT INTO user_hobbies (user_id,hobby_id,interest_level) VALUES %s",
    user_hobbies
)
conn.commit()
print("✅ User hobbies assigned")

# --------------------------
# EVENTS
# --------------------------
events = []
for _ in range(NUM_EVENTS):
    uid = random.choice(user_ids)
    start = fake.date_time_this_year()
    end = start + timedelta(hours=random.randint(1,6))
    events.append((
        fake.sentence(nb_words=4),
        random.choice(hobbies_list),
        fake.city(),
        fake.country(),
        round(fake.latitude(),6),
        round(fake.longitude(),6),
        start,
        end,
        uid
    ))

execute_values(cur,
    """INSERT INTO events 
    (event_name, category, city, country, latitude, longitude, start_time, end_time, organiser_id)
    VALUES %s""",
    events
)
conn.commit()
print("✅ Events generated")

# --------------------------
# USER_EVENTS (attendance, payment, feedback)
# --------------------------
cur.execute("SELECT event_id FROM events")
event_ids = [row[0] for row in cur.fetchall()]

user_events = []
payment_methods = ["cash","PayPal","Stripe","crypto"]
for eid in event_ids:
    attendees = random.sample(user_ids, k=random.randint(5,15))
    for uid in attendees:
        user_events.append((
            uid,
            eid,
            random.randint(1,5),            # rating
            fake.sentence(nb_words=8),       # feedback
            random.choice(payment_methods),  # payment_method
            round(random.uniform(10,500),2)  # amount_paid
        ))

execute_values(cur,
    """INSERT INTO user_events
    (user_id,event_id,rating,feedback,payment_method,amount_paid)
    VALUES %s""",
    user_events
)
conn.commit()
print("✅ User events (attendance & feedback) generated")

# --------------------------
# BLOGS
# --------------------------
blogs = []
for _ in range(NUM_BLOGS):
    author_id = random.choice(user_ids)
    blogs.append((author_id, fake.sentence(nb_words=6), fake.paragraph(nb_sentences=5), datetime.now()))

execute_values(cur,
    "INSERT INTO blogs (author_id,title,content,created_at) VALUES %s",
    blogs
)
conn.commit()
print("✅ Blogs generated")

# --------------------------
# BLOG_INTERACTIONS
# --------------------------
cur.execute("SELECT blog_id FROM blogs")
blog_ids = [row[0] for row in cur.fetchall()]

blog_interactions = []
for bid in blog_ids:
    interacting_users = random.sample(user_ids, k=random.randint(5,15))
    for uid in interacting_users:
        liked = random.choice([True, False])
        commented = fake.sentence(nb_words=10) if random.random()<0.5 else None
        blog_interactions.append((uid,bid,liked,commented))

execute_values(cur,
    "INSERT INTO blog_interactions (user_id, blog_id, liked, commented) VALUES %s",
    blog_interactions
)
conn.commit()
print("✅ Blog interactions generated")

# --------------------------
# ADS
# --------------------------
ads = []
for _ in range(NUM_ADS):
    advertiser_id = random.choice(user_ids)
    ads.append((advertiser_id, random.choice(hobbies_list), "18-45", fake.city(), round(random.uniform(50,1000),2), datetime.now()))

execute_values(cur,
    "INSERT INTO ads (advertiser_id,target_hobby,target_age_range,target_location,budget,created_at) VALUES %s",
    ads
)
conn.commit()
print("✅ Ads generated")

# --------------------------
# AD_INTERACTIONS
# --------------------------
cur.execute("SELECT ad_id FROM ads")
ad_ids = [row[0] for row in cur.fetchall()]

ad_interactions = []
for aid in ad_ids:
    interacting_users = random.sample(user_ids, k=random.randint(5,15))
    for uid in interacting_users:
        ad_interactions.append((uid,aid,random.choice([True,False]),random.choice([True,False])))

execute_values(cur,
    "INSERT INTO ad_interactions (user_id, ad_id, clicked, converted) VALUES %s",
    ad_interactions
)
conn.commit()
print("✅ Ad interactions generated")

# --------------------------
# REFERRALS
# --------------------------
referrals = []
for _ in range(int(NUM_USERS/2)):
    referrer, referred = random.sample(user_ids,2)
    referrals.append((None if referrer==referred else referrer, referred, random.choice([True,False]), datetime.now()))

execute_values(cur,
    "INSERT INTO referrals (referrer_id, referred_id, reward_given, created_at) VALUES %s",
    referrals
)
conn.commit()
print("✅ Referrals generated")

cur.close()
conn.close()
print("✅ Full synthetic Kumele data generation finished")
