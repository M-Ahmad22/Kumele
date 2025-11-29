# services/prediction/data_loader.py

import pandas as pd
from sqlalchemy import text
from app.db.database import local_engine

# Load events + interactions to build training dataset
def load_training_data():
    sql = """
    SELECT 
        e.event_id,
        e.event_name AS title,
        e.category AS hobby_category,
        e.city AS location,
        e.latitude,
        e.longitude,
        e.start_time,
        e.end_time,
        e.organiser_id AS host_id,

        -- RSVPs (yes only)
        COALESCE((
            SELECT COUNT(*) 
            FROM event_rsvp_logs r 
            WHERE r.event_id = e.event_id 
            AND r.rsvp_status = TRUE
        ), 0) AS rsvp_count,

        -- Attendance (showed up)
        COALESCE((
            SELECT COUNT(*) 
            FROM event_attendance_logs a 
            WHERE a.event_id = e.event_id 
            AND a.attended = TRUE
        ), 0) AS attendance,

        -- Ratings from user_events
        COALESCE((
            SELECT AVG(ue.rating)::float
            FROM user_events ue 
            WHERE ue.event_id = e.event_id
        ), 0) AS avg_rating

    FROM events e;
    """

    df = pd.read_sql(text(sql), local_engine)
    return df

def load_timeseries_daily():
    sql = "SELECT * FROM timeseries_daily ORDER BY ts;"
    return pd.read_sql(text(sql), local_engine)
