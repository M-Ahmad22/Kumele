from pydantic import BaseModel

class EventInput(BaseModel):
    event_title: str
    hobby: str
    date: str     # YYYY-MM-DD
    time: str     # HH:MM
    location: str
    is_paid: bool
    host_past_events: int
    avg_host_rating: float

class AttendanceResponse(BaseModel):
    predicted_attendance: int
    confidence_interval: list[int]

class TrendItem(BaseModel):
    day: str
    time_range: str
    avg_attendance: float

class TrendsResponse(BaseModel):
    hobby: str
    location: str
    recommended_times: list[TrendItem]
