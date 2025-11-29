import random
from datetime import datetime
from sqlalchemy import text
from app.db.database import local_engine

def generate_discount_history():
    conn = local_engine.connect()

    events = conn.execute(text("SELECT event_id, organiser_id, category, city, capacity FROM events")).fetchall()
    if not events:
        print("No events found.")
        return

    segments = ["Gold users", "Silver users", "Bronze users", "New users"]

    for e in events:
        for _ in range(5):
            discount = random.randint(5, 25)
            uplift = random.uniform(0.05, 0.30)

            conn.execute(
                text("""
                    INSERT INTO discount_suggestions (
                        event_id, discount_type, value_percent,
                        segment, expected_uplift
                    ) VALUES (
                        :eid, :dtype, :val,
                        :seg, :uplift
                    )
                """),
                {
                    "eid": e.event_id,
                    "dtype": "Loyalty",
                    "val": discount,
                    "seg": random.choice(segments),
                    "uplift": uplift
                }
            )

    conn.commit()
    conn.close()
    print("✔ Discount synthetic data generated.")

if __name__ == "__main__":
    generate_discount_history()
