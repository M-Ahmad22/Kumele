from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import text
from app.db.database import local_engine


def fetch_trends(timeframe="7d", location=None, limit=20):
    days = int(timeframe.replace("d", ""))
    cutoff = datetime.utcnow() - timedelta(days=days)

    sql = """
        SELECT topic, current_mentions AS mentions, trend_score
        FROM nlp_trends
        WHERE computed_at >= :cut
        ORDER BY trend_score DESC
        LIMIT :lim
    """

    df = pd.read_sql(
        text(sql),
        local_engine,
        params={"cut": cutoff, "lim": limit}
    )

    return {
        "timeframe": timeframe,
        "location": location,
        "trends": df.to_dict(orient="records")
    }
