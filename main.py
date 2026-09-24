# ==============================================================================
# Project: AlgoForge Pro Enterprise
# Author & Copyright Owner: Keshav Gupta (c) 2026
# All Rights Reserved. Unauthorized copying, distribution, or claiming authorship
# of this software architecture is strictly prohibited by copyright law.
# ==============================================================================
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
from typing import List, Optional
import hashlib
import secrets
import random

import models, schemas
from database import engine, get_db

# Initialize database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AlgoForge Pro Enterprise API")
templates = Jinja2Templates(directory="templates")

# Native PBKDF2 Password Hashing (Zero third-party dependency issues)
def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return f"{salt}${key.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        salt, key_hex = hashed_password.split('$')
        new_key = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return secrets.compare_digest(new_key.hex(), key_hex)
    except Exception:
        return False

INTERVALS = [1, 3, 7, 14, 30]

# Expanded Placement Problem Reservoir
RESERVOIR = [
    {"title": "Two Sum", "topic": "Arrays & Hashing", "difficulty": "Easy", "platform": "LeetCode", "url": "https://leetcode.com/problems/two-sum"},
    {"title": "Valid Anagram", "topic": "Strings & Hashing", "difficulty": "Easy", "platform": "LeetCode", "url": "https://leetcode.com/problems/valid-anagram"},
    {"title": "Reverse Linked List", "topic": "Linked Lists", "difficulty": "Easy", "platform": "LeetCode", "url": "https://leetcode.com/problems/reverse-linked-list"},
    {"title": "Valid Parentheses", "topic": "Stacks", "difficulty": "Easy", "platform": "LeetCode", "url": "https://leetcode.com/problems/valid-parentheses"},
    {"title": "Binary Search", "topic": "Binary Search", "difficulty": "Easy", "platform": "LeetCode", "url": "https://leetcode.com/problems/binary-search"},
    {"title": "Maximum Subarray (Kadane's)", "topic": "Dynamic Programming", "difficulty": "Medium", "platform": "LeetCode", "url": "https://leetcode.com/problems/maximum-subarray"},
    {"title": "3Sum", "topic": "Two Pointers", "difficulty": "Medium", "platform": "LeetCode", "url": "https://leetcode.com/problems/3sum"},
    {"title": "Longest Substring Without Repeating Characters", "topic": "Sliding Window", "difficulty": "Medium", "platform": "LeetCode", "url": "https://leetcode.com/problems/longest-substring-without-repeating-characters"},
    {"title": "Container With Most Water", "topic": "Two Pointers", "difficulty": "Medium", "platform": "LeetCode", "url": "https://leetcode.com/problems/container-with-most-water"},
    {"title": "Number of Islands", "topic": "Graphs (BFS/DFS)", "difficulty": "Medium", "platform": "LeetCode", "url": "https://leetcode.com/problems/number-of-islands"},
    {"title": "Kth Largest Element in an Array", "topic": "Heaps & Quickselect", "difficulty": "Medium", "platform": "LeetCode", "url": "https://leetcode.com/problems/kth-largest-element-in-an-array"},
    {"title": "LRU Cache", "topic": "System & Data Structure Design", "difficulty": "Medium", "platform": "LeetCode", "url": "https://leetcode.com/problems/lru-cache"},
    {"title": "Trapping Rain Water", "topic": "Monotonic Stack", "difficulty": "Hard", "platform": "LeetCode", "url": "https://leetcode.com/problems/trapping-rain-water"},
    {"title": "Word Ladder", "topic": "Graph BFS Shortest Path", "difficulty": "Hard", "platform": "LeetCode", "url": "https://leetcode.com/problems/word-ladder"},
    {"title": "Merge k Sorted Lists", "topic": "Heaps / Divide & Conquer", "difficulty": "Hard", "platform": "LeetCode", "url": "https://leetcode.com/problems/merge-k-sorted-lists"}
]

@app.get("/", response_class=HTMLResponse)
def serve_dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

# --- AUTHENTICATION APIS ---
@app.post("/auth/register")
def register_user(data: schemas.UserRegister, db: Session = Depends(get_db)):
    existing = db.query(models.UserProfile).filter(models.UserProfile.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered.")
    
    hashed = hash_password(data.password)
    level = "Beginner"
    if data.solved_count >= 150:
        level = "Advanced"
    elif data.solved_count >= 50:
        level = "Intermediate"

    user = models.UserProfile(
        username=data.username,
        hashed_password=hashed,
        name=data.name,
        primary_language=data.primary_language,
        target_role=data.target_role,
        solved_count=data.solved_count,
        experience_level=level
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "Account created successfully", "user_id": user.id, "username": user.username}

@app.post("/auth/login")
def login_user(data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.UserProfile).filter(models.UserProfile.username == data.username).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    return {
        "message": "Login successful",
        "user_id": user.id,
        "name": user.name,
        "username": user.username,
        "primary_language": user.primary_language,
        "experience_level": user.experience_level
    }

@app.get("/profile/")
def get_profile(db: Session = Depends(get_db)):
    profile = db.query(models.UserProfile).first()
    if not profile:
        profile = models.UserProfile(
            username="candidate",
            hashed_password=hash_password("admin123"),
            name="Keshav Gupta",
            solved_count=25,
            primary_language="C++",
            target_role="Software Development Engineer",
            experience_level="Beginner"
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile

@app.put("/profile/")
def update_profile(data: schemas.ProfileUpdate, db: Session = Depends(get_db)):
    profile = db.query(models.UserProfile).first()
    if not profile:
        profile = models.UserProfile(username="candidate", hashed_password=hash_password("pass"))
        db.add(profile)
    
    profile.name = data.name
    profile.solved_count = data.solved_count
    profile.target_role = data.target_role
    profile.primary_language = data.primary_language
    
    if data.solved_count < 50:
        profile.experience_level = "Beginner"
    elif data.solved_count <= 150:
        profile.experience_level = "Intermediate"
    else:
        profile.experience_level = "Advanced"
        
    db.commit()
    db.refresh(profile)
    return profile

# --- SMART DISCOVERY APIS ---
@app.get("/recommendations/")
def get_recommendations(level: str = "Beginner"):
    if "Beginner" in level:
        return [p for p in RESERVOIR if p["difficulty"] == "Easy"][:6]
    elif "Intermediate" in level:
        return [p for p in RESERVOIR if p["difficulty"] == "Medium"][:6]
    else:
        return [p for p in RESERVOIR if p["difficulty"] in ["Medium", "Hard"]][:6]

@app.get("/discover/random")
def get_random_challenge():
    return random.choice(RESERVOIR)

# --- CALENDAR & PROBLEMS APIS ---
@app.get("/calendar/activity/")
def get_calendar_activity(db: Session = Depends(get_db)):
    results = db.query(models.Problem.solved_date, func.count(models.Problem.id)).group_by(models.Problem.solved_date).all()
    return {str(r[0]): r[1] for r in results if r[0] is not None}

@app.post("/problems/", response_model=schemas.ProblemResponse)
def log_problem(problem: schemas.ProblemCreate, db: Session = Depends(get_db)):
    today = date.today()
    next_review = today + timedelta(days=INTERVALS[0])
    
    db_problem = models.Problem(
        **problem.model_dump(),
        solved_date=today,
        next_review_date=next_review,
        revision_count=0
    )
    db.add(db_problem)
    
    target = db.query(models.DailyTarget).filter(models.DailyTarget.target_date == today).first()
    if target:
        target.completed_count += 1
        
    db.commit()
    db.refresh(db_problem)
    return db_problem

@app.get("/problems/due-today/", response_model=List[schemas.ProblemResponse])
def get_due_problems(db: Session = Depends(get_db)):
    today = date.today()
    return db.query(models.Problem).filter(models.Problem.next_review_date <= today).all()

@app.put("/problems/{problem_id}/revise", response_model=schemas.ProblemResponse)
def mark_problem_revised(problem_id: int, db: Session = Depends(get_db)):
    problem = db.query(models.Problem).filter(models.Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    problem.revision_count += 1
    gap = INTERVALS[problem.revision_count] if problem.revision_count < len(INTERVALS) else 45
    problem.next_review_date = date.today() + timedelta(days=gap)
    db.commit()
    db.refresh(problem)
    return problem

@app.delete("/problems/{problem_id}")
def delete_problem(problem_id: int, db: Session = Depends(get_db)):
    problem = db.query(models.Problem).filter(models.Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    db.delete(problem)
    db.commit()
    return {"message": "Problem removed successfully"}

# BULK PURGE ALL TRACKED PROBLEMS
@app.delete("/problems/all/purge")
def purge_all_problems(db: Session = Depends(get_db)):
    deleted_count = db.query(models.Problem).delete()
    db.commit()
    return {"message": f"Successfully deleted all {deleted_count} problem records."}

@app.get("/problems/", response_model=List[schemas.ProblemResponse])
def get_all_problems(topic: Optional[str] = None, solved_date: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.Problem)
    if topic:
        query = query.filter(models.Problem.topic.ilike(f"%{topic}%"))
    if solved_date:
        query = query.filter(models.Problem.solved_date == solved_date)
    return query.all()

# --- TARGET APIS ---
@app.get("/target/")
def get_target(db: Session = Depends(get_db)):
    today = date.today()
    target = db.query(models.DailyTarget).filter(models.DailyTarget.target_date == today).first()
    if not target:
        target = models.DailyTarget(target_date=today, target_count=3, completed_count=0)
        db.add(target)
        db.commit()
        db.refresh(target)
    return target

@app.post("/target/")
def set_target(count: int, db: Session = Depends(get_db)):
    today = date.today()
    target = db.query(models.DailyTarget).filter(models.DailyTarget.target_date == today).first()
    if target:
        target.target_count = count
    else:
        target = models.DailyTarget(target_date=today, target_count=count, completed_count=0)
        db.add(target)
    db.commit()
    return target