# # app/services/ads/audience_matcher.py

# from typing import List, Dict, Optional
# import math

# import pandas as pd
# from sqlalchemy import text

# from app.db.database import local_engine


# def get_audience_match(ad_id: int) -> Optional[List[Dict]]:
#     """
#     Build audience segments for a given ad_id using real users and hobbies.

#     Uses:
#       - ads.target_hobby
#       - ads.target_location (city text)
#       - users.age, users.gender, users.city
#       - user_hobbies + hobbies

#     Returns top segments like:
#       {
#         "segment": "Women, 25-34, Berlin, Yoga",
#         "match_score": 0.87,
#         "audience_size": 4520
#       }
#     """

#     # Load ad
#     ad_sql = text("""
#         SELECT ad_id, target_hobby, target_location, target_age_range, budget
#         FROM ads
#         WHERE ad_id = :ad_id
#         LIMIT 1;
#     """)

#     ad_df = pd.read_sql(ad_sql, local_engine, params={"ad_id": ad_id})

#     if ad_df.empty:
#         return None

#     ad = ad_df.iloc[0]
#     ad_hobby = (ad["target_hobby"] or "").strip()
#     ad_location = (ad["target_location"] or "").strip()

#     # Load users + hobbies
#     sql = text("""
#         SELECT 
#             u.user_id,
#             u.age,
#             u.gender,
#             u.city,
#             h.hobby_name
#         FROM users u
#         LEFT JOIN user_hobbies uh ON uh.user_id = u.user_id
#         LEFT JOIN hobbies h ON h.hobby_id = uh.hobby_id;
#     """)

#     df = pd.read_sql(sql, local_engine)

#     if df.empty:
#         return []

#     # Age bucket
#     def age_bucket(age):
#         try:
#             a = int(age)
#         except Exception:
#             return "25-34"
#         if a < 18:
#             return "13-17"
#         if a < 25:
#             return "18-24"
#         if a < 35:
#             return "25-34"
#         if a < 45:
#             return "35-44"
#         if a < 55:
#             return "45-54"
#         return "55+"

#     df["age_bucket"] = df["age"].apply(age_bucket)
#     df["gender"] = df["gender"].fillna("Mixed")
#     df["city"] = df["city"].fillna("Unknown")
#     df["hobby_name"] = df["hobby_name"].fillna("General")

#     # Group into segments
#     grouped = df.groupby(["gender", "age_bucket", "city", "hobby_name"]).agg(
#         audience_size=("user_id", "nunique")
#     ).reset_index()

#     segments = []

#     for _, row in grouped.iterrows():
#         gender = row["gender"]
#         age_b = row["age_bucket"]
#         city = row["city"]
#         hobby = row["hobby_name"]

#         # Matching score: simple heuristic
#         score = 0.3  # base

#         # Hobby similarity
#         if ad_hobby and hobby.lower() == ad_hobby.lower():
#             score += 0.4
#         elif ad_hobby and ad_hobby.lower() in hobby.lower():
#             score += 0.25

#         # Location similarity (city text)
#         if ad_location and city and city.lower() == ad_location.lower():
#             score += 0.2
#         elif ad_location and city and ad_location.lower() in city.lower():
#             score += 0.1

#         # Age target from ad (rough)
#         if ad["target_age_range"]:
#             target_str = str(ad["target_age_range"])
#             if age_b in target_str:
#                 score += 0.1

#         score = min(score, 1.0)

#         segments.append({
#             "segment": f"{gender}, {age_b}, {city}, {hobby}",
#             "match_score": round(score, 2),
#             "audience_size": int(row["audience_size"])
#         })

#     # Sort by match_score, then audience_size
#     segments = sorted(segments, key=lambda x: (x["match_score"], x["audience_size"]), reverse=True)

#     # Return top 10
#     return segments[:10]

import pandas as pd
from sqlalchemy import text
from app.db.database import local_engine


def get_audience_match(ad_id: int):
    sql_ad = text("""
        SELECT target_hobby, target_location, target_age_range
        FROM ads WHERE ad_id = :id LIMIT 1
    """)
    ad_df = pd.read_sql(sql_ad, local_engine, params={"id": ad_id})

    if ad_df.empty:
        return None

    ad = ad_df.iloc[0]
    hobby = (ad["target_hobby"] or "").lower()
    location = (ad["target_location"] or "").lower()

    sql_users = text("""
        SELECT u.user_id, u.age, u.gender, u.city, h.hobby_name
        FROM users u
        LEFT JOIN user_hobbies uh ON uh.user_id = u.user_id
        LEFT JOIN hobbies h ON h.hobby_id = uh.hobby_id
    """)
    df = pd.read_sql(sql_users, local_engine)

    df["gender"] = df["gender"].fillna("Mixed")
    df["city"] = df["city"].fillna("Unknown")
    df["hobby_name"] = df["hobby_name"].fillna("General")

    def bucket(a):
        try:
            a = int(a)
        except:
            return "25-34"
        if a < 18: return "13-17"
        if a < 25: return "18-24"
        if a < 35: return "25-34"
        if a < 45: return "35-44"
        if a < 55: return "45-54"
        return "55+"

    df["age_bucket"] = df["age"].apply(bucket)

    grouped = df.groupby(["gender", "age_bucket", "city", "hobby_name"]).agg(
        audience_size=("user_id", "nunique")
    ).reset_index()

    out = []
    for _, row in grouped.iterrows():
        score = 0.3
        if row["hobby_name"].lower() == hobby: score += 0.4
        if location in row["city"].lower(): score += 0.2
        out.append({
            "segment": f"{row['gender']}, {row['age_bucket']}, {row['city']}, {row['hobby_name']}",
            "match_score": round(score, 2),
            "audience_size": int(row["audience_size"])
        })

    return sorted(out, key=lambda x: (x["match_score"], x["audience_size"]), reverse=True)[:10]
