import pandas as pd
from sqlalchemy import text
from app.db.database import local_engine

def build_timeseries_daily():
    sql = """
    SELECT
        DATE(e.start_time) AS ts,
        COUNT(e.event_id) AS total_events,
        COALESCE((
            SELECT COUNT(*) FROM event_rsvp_logs r
            WHERE r.event_id = e.event_id AND r.rsvp_status = TRUE
        ),0) AS rsvp,
        COALESCE((
            SELECT COUNT(*) FROM event_attendance_logs a
            WHERE a.event_id = e.event_id AND a.attended = TRUE
        ),0) AS attended
    FROM events e
    GROUP BY DATE(e.start_time), e.event_id
    """

    df = pd.read_sql(text(sql), local_engine)

    ts = df.groupby("ts").agg({
        "total_events": "sum",
        "rsvp": "sum",
        "attended": "sum"
    }).reset_index()

    ts.columns = ["ts", "total_events", "total_rsvps", "total_attendance"]

    ts.to_sql("timeseries_daily", local_engine, if_exists="replace", index=False)

    print("✅ timeseries_daily built successfully.")
