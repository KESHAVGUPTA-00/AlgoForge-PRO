# ==============================================================================
# Project: AlgoForge Pro Enterprise
# Author & Copyright Owner: Keshav Gupta (c) 2026
# All Rights Reserved. Unauthorized copying, distribution, or claiming authorship
# of this software architecture is strictly prohibited by copyright law.
# ==============================================================================
# ==============================================================================
# Project: AlgoForge Pro Enterprise
# Author & Copyright Owner: Keshav Gupta (c) 2026
# All Rights Reserved.
# ==============================================================================
from pydantic import BaseModel
from datetime import date
from typing import Optional

class ProblemBase(BaseModel):
    title: str
    platform: Optional[str] = "LeetCode"
    topic: str
    difficulty: str
    problem_url: Optional[str] = None
    notes: Optional[str] = None
    code_snippet: Optional[str] = None
    pattern_tag: Optional[str] = "General"

class ProblemCreate(ProblemBase):
    pass

class ProblemResponse(ProblemBase):
    id: int
    solved_date: date
    next_review_date: date
    revision_count: int

    class Config:
        from_attributes = True

class UserRegister(BaseModel):
    username: str
    password: str
    name: str
    phone_number: Optional[str] = None
    primary_language: str
    target_role: str
    solved_count: int

class UserLogin(BaseModel):
    username: str
    password: str

class ProfileUpdate(BaseModel):
    name: str
    solved_count: int
    target_role: str
    primary_language: str