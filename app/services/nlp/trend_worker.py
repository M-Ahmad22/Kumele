import time
from datetime import date
from collections import defaultdict
import redis
import psycopg2

from app.config import REDIS_URL, LOCAL_DB_URL

STREAM = "nlp_events"
GROUP = "nlp-trend-group"
CONSUMER = "worker-1"
INTERVAL = 30

redis_client = redis.from_url(REDIS_URL)
pg = psycopg2.connect(LOCAL_DB_URL)
pg.autocommit = True

counters = defaultdict(lambda: {"mentions": 0, "weighted": 0})


def ensure_group():
    try:
        redis_client.xgroup_create(STREAM, GROUP, "0", mkstream=True)
    except:
        pass


def process(mid, f):
    topic = f[b"topic"].decode()
    ttype = f[b"topic_type"].decode()
    loc = f[b"location"].decode()
    rel = float(f[b"relevance"].decode())
    pol = float(f[b"polarity"].decode())
    ds = date.today().isoformat()

    key = (topic, ttype, loc, ds)
    counters[key]["mentions"] += 1
    counters[key]["weighted"] += rel * pol


def flush():
    cur = pg.cursor()
    for (topic, ttype, loc, ds), v in list(counters.items()):
        cur.execute("""
            INSERT INTO nlp_topic_daily (topic, ds, mentions)
            VALUES (%s, %s, %s)
            ON CONFLICT (topic, ds)
            DO UPDATE SET mentions = nlp_topic_daily.mentions + EXCLUDED.mentions
        """, (topic, ds, v["mentions"]))

        cur.execute("""
            INSERT INTO nlp_trends (topic, first_seen, last_seen, current_mentions, trend_score)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (topic)
            DO UPDATE SET
                last_seen = EXCLUDED.last_seen,
                current_mentions = nlp_trends.current_mentions + EXCLUDED.current_mentions,
                trend_score = nlp_trends.trend_score + EXCLUDED.trend_score
        """, (topic, ds, ds, v["mentions"], v["weighted"]))

        del counters[(topic, ttype, loc, ds)]
    cur.close()


def run():
    ensure_group()
    last = time.time()
    print("🚀 Trend worker running...")

    while True:
        msgs = redis_client.xreadgroup(GROUP, CONSUMER, {STREAM: ">"}, count=100, block=1000)
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
