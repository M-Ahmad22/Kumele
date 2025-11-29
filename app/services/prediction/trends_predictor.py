# app/services/prediction/trends_predictor.py

import pandas as pd
from sqlalchemy import text
from app.db.database import local_engine

# ---------------------------------------------------------
# Fetch aggregated attendance data for hobby + location
# ---------------------------------------------------------
def predict_best_times(hobby: str, location: str):
    sql = """
    SELECT 
        DATE(e.start_time) AS event_date,
        EXTRACT(DOW FROM e.start_time) AS dow,
        EXTRACT(HOUR FROM e.start_time) AS hour,
        e.category AS hobby,
        e.city AS location,
        (
            SELECT COUNT(*) FROM event_attendance_logs a
            WHERE a.event_id = e.event_id AND a.attended = TRUE
        ) AS attendance
    FROM events e
    WHERE e.category ILIKE :hobby
      AND e.city ILIKE :location;
    """

    df = pd.read_sql(text(sql), local_engine, params={
        "hobby": hobby,
        "location": location
    })

    if df.empty:
        return []   # ----------------- IMPORTANT ------------------

    # Map day index → name
    day_map = {
        0: "Sunday", 1: "Monday", 2: "Tuesday",
        3: "Wednesday", 4: "Thursday", 5: "Friday", 6: "Saturday"
    }

    df["day"] = df["dow"].map(day_map)
    df["time_range"] = df["hour"].apply(lambda h: f"{int(h):02d}:00 - {int(h)+2:02d}:00")

    grouped = df.groupby(["day", "time_range"], as_index=False)["attendance"].mean()

    # Sort by best avg attendance
    grouped = grouped.sort_values("attendance", ascending=False)

    # Convert to expected API format
    results = [
        {
            "day": row["day"],
            "time_range": row["time_range"],
            "avg_attendance": float(row["attendance"])
        }
        for _, row in grouped.iterrows()
    ]

    return results[:5]   # top 5 recommendations
