from pydantic import BaseModel
from typing import List, Optional, Dict, Any


# ---------------------------------------------------------
# ✅ Existing Schemas (Already Correct)
# ---------------------------------------------------------

class HobbyRecommendation(BaseModel):
    hobby: str
    score: float


class EventRecommendation(BaseModel):
    event_id: int
    title: str
    hobby: str
    score: float


class HobbyResponse(BaseModel):
    user_id: int
    recommended_hobbies: List[HobbyRecommendation]


class EventResponse(BaseModel):
    user_id: int
    recommended_events: List[EventRecommendation]


class MatchUserItem(BaseModel):
    user_id: int
    name: str
    hobbies: List[str]
    reward_status: Optional[str]
    gold_count: int
    match_score: float


class MatchUsersResponse(BaseModel):
    user_id: int
    cluster_id: int
    neighbors: List[MatchUserItem]


class MatchEventItem(BaseModel):
    event_id: int
    title: str
    hobby: str
    distance_km: float
    match_score: float


class MatchEventsResponse(BaseModel):
    user_id: int
    matched_events: List[MatchEventItem]


# ---------------------------------------------------------
# ✅ Moderation API Schemas (NEW)
# ---------------------------------------------------------

class ModerationCreateRequest(BaseModel):
    content_id: str
    type: str               # "text" or "image"
    subtype: Optional[str]  # blog, comment, event_banner, etc.
    data: str               # Text content OR base64 image OR URL


class ModerationQueuedResponse(BaseModel):
    content_id: str
    status: str = "pending"
    message: str = "Moderation job queued"


class ModerationStatusResponse(BaseModel):
    content_id: str
    status: str             # pending | completed | failed
    decision: Optional[str] # approve | reject | needs_review
    labels: Optional[Dict[str, float]]  # { "toxicity":0.10, "spam":0.02 }



class ModerationRequest(BaseModel):
    content_id: str
    type: str   # "text" or "image"
    subtype: Optional[str] = None
    data: str   # text or base64/url for image

class ModerationStatusResponse(BaseModel):
    content_id: str
    status: str
    decision: Optional[str] = None
    labels: Optional[Dict[str, Any]] = None
    worker_notes: Optional[str] = None