# # app/db/database.py

# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, declarative_base
# from app import config

# Base = declarative_base()

# # -----------------------
# # DATABASE ENGINES
# # -----------------------
# real_engine = create_engine(
#     config.REAL_DB_URL,
#     future=True
# )

# local_engine = create_engine(
#     config.LOCAL_DB_URL,
#     future=True
# )


# engine = local_engine


# # -----------------------
# # SESSION FACTORIES
# # -----------------------
# RealSessionLocal = sessionmaker(
#     autocommit=False, autoflush=False,
#     bind=real_engine, future=True
# )

# LocalSessionLocal = sessionmaker(
#     autocommit=False, autoflush=False,
#     bind=local_engine, future=True
# )


# # -----------------------
# # FASTAPI DEPENDENCIES
# # -----------------------
# def get_real_db():
#     db = RealSessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


# def get_local_db():
#     db = LocalSessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# app/db/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app import config

Base = declarative_base()

# -----------------------
# DATABASE ENGINES
# -----------------------

# REAL DB (unchanged)
real_engine = create_engine(
    config.REAL_DB_URL,
    future=True
)

# LOCAL / NEON DB (FIXED)
local_engine = create_engine(
    config.LOCAL_DB_URL,
    pool_pre_ping=True,     # ✅ Detects dead connections and reconnects
    pool_recycle=300,       # ✅ Recycle every 5 minutes (Neon auto-closes idle)
    future=True
)

engine = local_engine   # your default


# -----------------------
# SESSION FACTORIES
# -----------------------

RealSessionLocal = sessionmaker(
    autocommit=False, autoflush=False,
    bind=real_engine, future=True
)

LocalSessionLocal = sessionmaker(
    autocommit=False, autoflush=False,
    bind=local_engine, future=True
)


# -----------------------
# FASTAPI DEPENDENCIES
# -----------------------

def get_real_db():
    db = RealSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_local_db():
    db = LocalSessionLocal()
    try:
        yield db
    finally:
        db.close()
