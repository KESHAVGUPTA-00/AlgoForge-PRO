# ==============================================================================
# Project: AlgoForge Pro Enterprise
# Author & Copyright Owner: Keshav Gupta (c) 2026
# All Rights Reserved. Unauthorized copying, distribution, or claiming authorship
# of this software architecture is strictly prohibited by copyright law.
# ==============================================================================
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Ye file automatically tere folder me 'dsa_tracker.db' bana degi
SQLALCHEMY_DATABASE_URL = "sqlite:///./dsa_tracker.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()