# # app/db/database.py
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, declarative_base
# # from . import models
# # from . import models as _models
# import os
# from app import config

# Base = declarative_base()

# # Engines
# real_engine = create_engine(config.REAL_DB_URL, future=True)
# local_engine = create_engine(config.LOCAL_DB_URL, future=True)

# # Session factories
# RealSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=real_engine, future=True)
# LocalSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=local_engine, future=True)


# # Dependency for FastAPI to get a DB session (real DB)
# def get_real_db():
#     db = RealSessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# # Dependency for local DB (if needed)
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
real_engine = create_engine(
    config.REAL_DB_URL,
    future=True
)

local_engine = create_engine(
    config.LOCAL_DB_URL,
    future=True
)

# -----------------------
# COMPATIBILITY ALIAS
# -----------------------
# Some modules import `engine`, so we map it to `local_engine`
engine = local_engine


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
