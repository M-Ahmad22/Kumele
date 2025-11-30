# # app/services/match_service.py

# from app.services.geo_service import haversine_distance
# from app.services.embedding_service import get_embedding
# from app.core.scoring import encode_status, final_score
# from app.db.models import User, Event
# from app.services.tfrs_service import score_with_tfrs

# def match_events_for_user(db, user_id: int):
#     # Fetch user from DB
#     user = db.query(User).filter(User.user_id == user_id).first()
#     if not user:
#         return []

#     # Fetch all events
#     events = db.query(Event).all()
#     if not events:
#         return []

#     # Get user embedding (using hobbies if available)
#     user_hobbies_text = " ".join([h.hobby_name for h in getattr(user, "hobbies", [])]) if hasattr(user, "hobbies") else ""
#     user_emb = get_embedding(user_hobbies_text)

#     # Get embeddings for each event using event_name + category
#     event_embs = []
#     for e in events:
#         text = f"{e.event_name} {e.category}"
#         emb = get_embedding(text)
#         event_embs.append(emb[0] if isinstance(emb[0], list) else emb)

#     # Compute relevance scores using TFRS model
#     relevance_scores = score_with_tfrs(user_emb[0], event_embs)

#     results = []
#     for e, rel in zip(events, relevance_scores):
#         # Calculate geographical distance
#         dist_km = haversine_distance(user.latitude, user.longitude, e.latitude, e.longitude)

#         # Encode user and host status
#         user_status, user_gold_norm = encode_status(
#             getattr(user, "reward_status", "none"),
#             getattr(user, "gold_count", 0)
#         )
#         host_status, host_gold_norm = encode_status(
#             getattr(e, "host_status", "none"),
#             getattr(e, "host_gold_count", 0)
#         )

#         # Compute final score
#         user_score = user_status + 0.2 * user_gold_norm
#         host_score = host_status + 0.2 * host_gold_norm
#         score = final_score(rel, user_score, host_score, dist_km)

#         results.append({
#             "event_id": e.event_id,
#             "event_name": e.event_name,
#             "category": e.category,
#             "city": e.city,
#             "country": e.country,
#             "latitude": e.latitude,
#             "longitude": e.longitude,
#             "start_time": e.start_time,
#             "end_time": e.end_time,
#             "relevance": rel,
#             "distance_km": round(dist_km, 2),
#             "final_score": round(score, 4)
#         })

#     # Sort by final score descending
#     results.sort(key=lambda r: r["final_score"], reverse=True)

#     # Return top 10 matches
#     return results[:10]

import numpy as np
from app.services.geo_service import haversine_distance
from app.services.embedding_service import get_embedding
from app.core.scoring import cosine_similarity_basic, combine_basic_score
from app.services.tfrs_service import score_with_tfrs
from app.db.models import User, Event


# -----------------------------------------------------------
# 1) BASIC MATCHING — /match/events
# -----------------------------------------------------------
def match_events_for_user_basic(db, user_id: int):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        return []

    events = db.query(Event).all()
    if not events:
        return []

    # Get user embedding from hobbies
    user_hobbies = " ".join([h.hobby_name for h in getattr(user, "hobbies", [])])
    user_emb = get_embedding(user_hobbies)[0]

    results = []
    for e in events:
        event_emb = get_embedding(f"{e.event_name} {e.category}")[0]

        # cosine similarity
        sim = cosine_similarity_basic(user_emb, event_emb)

        # distance
        dist_km = haversine_distance(user.latitude, user.longitude, e.latitude, e.longitude)

        # final hybrid score
        final = combine_basic_score(sim, dist_km)

        results.append({
            "event_id": e.event_id,
            "event_name": e.event_name,
            "category": e.category,
            "similarity": float(sim),
            "distance_km": round(dist_km, 2),
            "score": round(final, 4)
        })

    return sorted(results, key=lambda x: x["score"], reverse=True)[:10]


# -----------------------------------------------------------
# 2) ML RECOMMENDATION — /recommendations/events
# -----------------------------------------------------------
def match_events_for_user_ml(db, user_id: int):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        return []

    events = db.query(Event).all()
    if not events:
        return []

    # User embedding
    user_hobbies = " ".join([h.hobby_name for h in getattr(user, "hobbies", [])])
    user_vec = get_embedding(user_hobbies)[0]

    event_vecs = []
    for e in events:
        emb = get_embedding(f"{e.event_name} {e.category}")[0]
        event_vecs.append(emb)

    # Run TFRS scoring
    relevance_scores = score_with_tfrs(user_vec, event_vecs)

    results = []
    for e, rel in zip(events, relevance_scores):
        dist_km = haversine_distance(user.latitude, user.longitude, e.latitude, e.longitude)

        # ML score = relevance - distance penalty
        final_score = float(rel) - (dist_km * 0.01)

        results.append({
            "event_id": e.event_id,
            "event_name": e.event_name,
            "category": e.category,
            "relevance": float(rel),
            "distance_km": round(dist_km, 2),
            "final_score": round(final_score, 4)
        })

    # highest score first
    return sorted(results, key=lambda x: x["final_score"], reverse=True)[:10]
