# ==============================================================================
# Project: AlgoForge Pro Enterprise
# Author & Copyright Owner: Keshav Gupta (c) 2026
# All Rights Reserved. Unauthorized copying, distribution, or claiming authorship
# of this software architecture is strictly prohibited by copyright law.
# ==============================================================================
from sqlalchemy import Column, Integer, String, Date, Text
from datetime import date
from database import Base

class Problem(Base):
    __tablename__ = "problems"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, default=1)
    title = Column(String, nullable=False)
    platform = Column(String, default="LeetCode")
    topic = Column(String, index=True)
    difficulty = Column(String)
    problem_url = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    
    solved_date = Column(Date, default=date.today)
    next_review_date = Column(Date, nullable=False)
    revision_count = Column(Integer, default=0)

class UserProfile(Base):
    __tablename__ = "user_profile"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    name = Column(String, default="Candidate")
    solved_count = Column(Integer, default=0)
    target_role = Column(String, default="Software Development Engineer")
    primary_language = Column(String, default="C++")  # C++, Java, Python, JavaScript
    experience_level = Column(String, default="Beginner")

class DailyTarget(Base):
    __tablename__ = "daily_targets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, default=1)
    target_date = Column(Date, default=date.today)
    target_count = Column(Integer, default=3)
    completed_count = Column(Integer, default=0)