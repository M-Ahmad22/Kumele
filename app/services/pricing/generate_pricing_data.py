import random
from datetime import datetime, timedelta
from sqlalchemy import text
from app.db.database import local_engine

def generate_pricing_history():
    conn = local_engine.connect()

    events = conn.execute(text("SELECT event_id, organiser_id, category, city, capacity FROM events")).fetchall()
    if not events:
        print("No events found. Insert some events first.")
        return

    for e in events:
        for _ in range(4):
            base_price = random.randint(500, 8000)
            turnout = random.randint(5, e.capacity)
            host_rating = round(random.uniform(2.5, 5.0), 2)
            revenue = base_price * turnout
            dt = datetime.now() - timedelta(days=random.randint(10, 300))

            conn.execute(
                text("""
                    INSERT INTO pricing_history (
                        event_id, host_id, category, city,
                        base_price, turnout, capacity,
                        host_rating, event_date, revenue
                    ) VALUES (
                        :eid, :hid, :cat, :city,
                        :price, :turnout, :cap,
                        :rating, :dt, :rev
                    )
                """),
                {
                    "eid": e.event_id,
                    "hid": e.organiser_id,
                    "cat": e.category,
                    "city": e.city,
                    "price": base_price,
                    "turnout": turnout,
                    "cap": e.capacity,
                    "rating": host_rating,
                    "dt": dt,
                    "rev": revenue
                }
            )

    conn.commit()
    conn.close()
    print("✔ Pricing history generated.")

if __name__ == "__main__":
    generate_pricing_history()
