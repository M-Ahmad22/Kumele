import os
import pickle
import numpy as np
from sqlalchemy import text
from sklearn.ensemble import RandomForestRegressor
from app.db.database import local_engine
from app.config import MODEL_DIR

MODEL_PATH = os.path.join(MODEL_DIR, "pricing_model.pkl")

def train_pricing_model():
    conn = local_engine.connect()
    rows = conn.execute(text("""
        SELECT base_price, turnout, host_rating, capacity
        FROM pricing_history
    """)).fetchall()
    conn.close()

    if len(rows) < 30:
        raise Exception("Need at least 30 rows of pricing history to train.")

    prices = np.array([[r.base_price, r.host_rating, r.capacity] for r in rows])
    turnout = np.array([r.turnout for r in rows])

    model = RandomForestRegressor(
        n_estimators=150,
        random_state=42,
        max_depth=10
    )
    model.fit(prices, turnout)

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)

    print("✔ Pricing model trained and saved:", MODEL_PATH)

if __name__ == "__main__":
    train_pricing_model()
