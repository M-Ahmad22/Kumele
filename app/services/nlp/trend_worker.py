import time
from datetime import date
from collections import defaultdict
import redis
import psycopg2

from app.config import REDIS_URL, LOCAL_DB_URL

STREAM = "nlp_events"
GROUP = "nlp-trend-group"
CONSUMER = "worker-1"
INTERVAL = 30  # flush every 30 seconds

redis_client = redis.from_url(REDIS_URL)
pg = psycopg2.connect(LOCAL_DB_URL)
pg.autocommit = True

# counters[(topic, ds)] = {"mentions": ..., "weighted": ...}
counters = defaultdict(lambda: {"mentions": 0, "weighted": 0})


def ensure_group():
    """Ensure the Redis stream consumer group exists."""
    try:
        redis_client.xgroup_create(STREAM, GROUP, "0", mkstream=True)
    except:
        pass  # already exists


def process(mid, f):
    """
    Normalize redis fields:
    - Old format: topic, topic_type, location, relevance, polarity
    - New format: keyword, type
    """
    # Extract topic name
    if b"topic" in f:
        topic = f[b"topic"].decode()
    elif b"keyword" in f:
        topic = f[b"keyword"].decode()
    else:
        print("⚠️ Skipped message: no topic/keyword field")
        return

    # Extract type
    if b"topic_type" in f:
        topic_type = f[b"topic_type"].decode()
    elif b"type" in f:
        topic_type = f[b"type"].decode()
    else:
        topic_type = "keyword"

    # Extract location (fallback)
    if b"location" in f:
        location = f[b"location"].decode()
    else:
        location = "global"

    # Extract relevance
    try:
        relevance = float(f.get(b"relevance", b"1.0"))
    except:
        relevance = 1.0

    # Extract polarity
    try:
        polarity = float(f.get(b"polarity", b"1.0"))
    except:
        polarity = 1.0

    ds = date.today().isoformat()  # YYYY-MM-DD

    key = (topic, ds)

    counters[key]["mentions"] += 1
    counters[key]["weighted"] += relevance * polarity

    print(f"🔥 Processed: {topic}")


def flush():
    cur = pg.cursor()

    for (topic, ds), v in list(counters.items()):
        mentions = v["mentions"]
        weighted = v["weighted"]

        # Insert/update daily mentions
        cur.execute("""
            INSERT INTO nlp_topic_daily (topic, ds, mentions)
            VALUES (%s, %s, %s)
            ON CONFLICT (topic, ds)
            DO UPDATE SET mentions = nlp_topic_daily.mentions + EXCLUDED.mentions
        """, (topic, ds, mentions))

        # Update trends table
        cur.execute("""
            INSERT INTO nlp_trends (topic, first_seen, last_seen, current_mentions, trend_score)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (topic)
            DO UPDATE SET
                last_seen = EXCLUDED.last_seen,
                current_mentions = nlp_trends.current_mentions + EXCLUDED.current_mentions,
                trend_score = nlp_trends.trend_score + EXCLUDED.trend_score
        """, (topic, ds, ds, mentions, weighted))

        # Clear counter
        del counters[(topic, ds)]

    cur.close()

    print(f"💾 Flushed trends ({len(counters)} topics)")


def run():
    ensure_group()
    last = time.time()

    print("🚀 Trend worker running...")

    while True:
        msgs = redis_client.xreadgroup(
            groupname=GROUP,
            consumername=CONSUMER,
            streams={STREAM: ">"},
            count=100,
            block=1000
        )

        if msgs:
            for stream, entries in msgs:
                for mid, f in entries:
                    process(mid, f)
                    redis_client.xack(STREAM, GROUP, mid)

        if time.time() - last >= INTERVAL:
            flush()
            last = time.time()


if __name__ == "__main__":
    run()
