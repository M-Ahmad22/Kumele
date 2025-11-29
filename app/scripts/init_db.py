# scripts/init_db.py
from app.db.database import local_engine, Base
from app.db import models_rewards

def create_all():
    print("Creating tables on local_engine DB...")
    Base.metadata.create_all(bind=local_engine)
    print("Done.")

if __name__ == "__main__":
    create_all()
