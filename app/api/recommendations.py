# """
# Handlers for:
# GET /recommendations/hobbies
# GET /recommendations/events

# These endpoints follow the spec:
# - /recommendations/hobbies => suggests hobbies for a user
# - /recommendations/events => suggests events for a user from the hybrid model
# """

# from fastapi import APIRouter, HTTPException, Query, Depends
# from typing import List
# from ..schemas import HobbyResponse, EventResponse, HobbyRecommendation, EventRecommendation
# from ..data.loader import load_users_csv, load_events_csv, build_inmemory_user_db, build_inmemory_event_db
# from ..utils import cosine_similarity
# from .. import config
# import numpy as np
# import os

# router = APIRouter()

# # ---- Simple in-memory model placeholders ----
# # In production, replace these with real model loaders that load:
# # - TFRS user tower to get user embedding
# # - Event embeddings index or event tower
# #
# # For now: read synthetic data and create naive embeddings (hashing)
# _USERS_CACHE = None
# _EVENTS_CACHE = None
# _USER_EMB_CACHE = {}
# _EVENT_EMB_CACHE = {}

# def init_caches():
#     global _USERS_CACHE, _EVENTS_CACHE
#     if _USERS_CACHE is None:
#         users_df = load_users_csv()
#         _USERS_CACHE = build_inmemory_user_db(users_df)
#     if _EVENTS_CACHE is None:
#         events_df = load_events_csv()
#         _EVENTS_CACHE = build_inmemory_event_db(events_df)

# def simple_user_embedding(user_dict):
#     # deterministic simple embedding from age and hobbies (placeholder)
#     key = f"user_{user_dict.get('name')}_{user_dict.get('age')}"
#     if key in _USER_EMB_CACHE:
#         return _USER_EMB_CACHE[key]
#     age = float(user_dict.get("age", 0))
#     hcount = len(user_dict.get("hobbies", []))
#     # map hobby names to simple floats
#     hvec = np.zeros(8)
#     for i, h in enumerate(user_dict.get("hobbies", [])[:8]):
#         hvec[i] = hash(h) % 100 / 100.0
#     emb = np.concatenate([[age/100.0, hcount/10.0], hvec[:6]])
#     _USER_EMB_CACHE[key] = emb
#     return emb

# def simple_event_embedding(event_dict):
#     key = f"event_{event_dict.get('title')}"
#     if key in _EVENT_EMB_CACHE:
#         return _EVENT_EMB_CACHE[key]
#     hobby = event_dict.get("hobby","")
#     emb = np.zeros(8)
#     emb[0] = (hash(hobby) % 100) / 100.0
#     emb[1] = float(event_dict.get("lat", 0.0)) / 90.0
#     emb[2] = float(event_dict.get("lon", 0.0)) / 180.0
#     _EVENT_EMB_CACHE[key] = emb
#     return emb

# @router.get("/recommendations/hobbies", response_model=HobbyResponse)
# def get_recommended_hobbies(user_id: int, top_n: int = Query(config.DEFAULT_TOP_N, gt=0, le=10)):
#     init_caches()
#     if user_id not in _USERS_CACHE:
#         raise HTTPException(status_code=404, detail="User not found")
#     u = _USERS_CACHE[user_id]
#     uemb = simple_user_embedding(u)
#     # candidate hobby list derived from event hobby distribution and user hobbies
#     candidates = set()
#     for ev in _EVENTS_CACHE.values():
#         if ev.get("hobby"):
#             candidates.add(ev["hobby"])
#     # Score each candidate by similarity to a hobby-proxy vector
#     scored = []
#     for hobby in candidates:
#         proxy = np.zeros_like(uemb)
#         proxy[0] = (hash(hobby) % 100) / 100.0
#         score = float(cosine_similarity(uemb, proxy))
#         scored.append({"hobby": hobby, "score": round(score,4)})
#     # include user's existing hobbies with boosted score
#     for h in u.get("hobbies", []):
#         scored.append({"hobby": h, "score": 0.9999})
#     scored = sorted(scored, key=lambda x: x["score"], reverse=True)
#     # deduplicate by hobby name
#     seen = set()
#     final = []
#     for s in scored:
#         if s["hobby"] in seen: continue
#         seen.add(s["hobby"])
#         final.append(s)
#         if len(final) >= top_n:
#             break
#     return {"user_id": user_id, "recommended_hobbies": final}

# @router.get("/recommendations/events", response_model=EventResponse)
# def get_recommended_events(user_id: int, top_n: int = Query(10, gt=0, le=50)):
#     """
#     Hybrid scoring:
#     - get user embedding (from TFRS user tower in prod; simple_user_embedding here)
#     - score candidate events by cosine similarity between embeddings
#     - rank and return top_n
#     """
#     init_caches()
#     if user_id not in _USERS_CACHE:
#         raise HTTPException(status_code=404, detail="User not found")
#     u = _USERS_CACHE[user_id]
#     uemb = simple_user_embedding(u)
#     scored = []
#     for eid, ev in _EVENTS_CACHE.items():
#         eemb = simple_event_embedding(ev)
#         score = float(cosine_similarity(uemb, eemb))
#         scored.append({
#             "event_id": int(eid),
#             "title": ev.get("title",""),
#             "hobby": ev.get("hobby",""),
#             "score": round(score, 4)
#         })
#     scored = sorted(scored, key=lambda x: x["score"], reverse=True)[:top_n]
#     return {"user_id": user_id, "recommended_events": scored}

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_local_db
from app.services.match_service import match_events_for_user

router = APIRouter(prefix="/recommendations", tags=["Event Recommendations"])

@router.get("/events")
def get_recommended_events(user_id: int = Query(...), db: Session = Depends(get_local_db)):
    data = match_events_for_user(db, user_id)
    return {"user_id": user_id, "recommendations": data}

