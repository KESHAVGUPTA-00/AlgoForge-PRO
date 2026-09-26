# ==============================================================================
# Project: AlgoForge Pro Enterprise
# Author & Copyright Owner: Keshav Gupta (c) 2026
# All Rights Reserved.
# ==============================================================================
import os
import hashlib
import sqlite3
import json
import urllib.request
from datetime import date, timedelta
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import engine, Base, get_db
import models
import schemas

# SQLite Schema Auto-Patcher for Multi-Language Code Columns
def auto_patch_database():
    db_file = "dsa_tracker.db"
    if os.path.exists(db_file):
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            cursor.execute("PRAGMA table_info(user_profile)")
            user_cols = [row[1] for row in cursor.fetchall()]
            if "phone_number" not in user_cols:
                cursor.execute("ALTER TABLE user_profile ADD COLUMN phone_number VARCHAR")
                
            cursor.execute("PRAGMA table_info(problems)")
            prob_cols = [row[1] for row in cursor.fetchall()]
            new_cols = [
                ("code_cpp", "TEXT"),
                ("code_python", "TEXT"),
                ("code_java", "TEXT"),
                ("code_snippet", "TEXT"),
                ("pattern_tag", "VARCHAR DEFAULT 'General'")
            ]
            for col_name, col_type in new_cols:
                if col_name not in prob_cols:
                    cursor.execute(f"ALTER TABLE problems ADD COLUMN {col_name} {col_type}")
                
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Migration Notice: {e}")

auto_patch_database()
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AlgoForge Pro Enterprise")

LEETCODE_GLOBAL_CACHE = {}

def sync_all_leetcode_questions():
    global LEETCODE_GLOBAL_CACHE
    try:
        url = "https://leetcode.com/api/problems/all/"
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            diff_map = {1: "Easy", 2: "Medium", 3: "Hard"}
            for item in data.get("stat_status_pairs", []):
                q_id = str(item["stat"]["frontend_question_id"])
                title = item["stat"]["question__title"]
                slug = item["stat"]["question__title_slug"]
                diff = diff_map.get(item.get("difficulty", {}).get("level", 2), "Medium")
                
                payload = {
                    "id": q_id,
                    "title": f"#{q_id}. {title}",
                    "difficulty": diff,
                    "topic": "Algorithms",
                    "pattern": "LeetCode Direct",
                    "url": f"https://leetcode.com/problems/{slug}/"
                }
                LEETCODE_GLOBAL_CACHE[q_id] = payload
                LEETCODE_GLOBAL_CACHE[title.lower()] = payload
                LEETCODE_GLOBAL_CACHE[slug.lower()] = payload
            print(f"✅ Successfully synchronized {len(LEETCODE_GLOBAL_CACHE)} LeetCode problems into memory!")
    except Exception as e:
        print(f"⚠️ LeetCode live sync notice: {e}. Fallback active.")

@app.on_event("startup")
async def startup_event():
    sync_all_leetcode_questions()

def hash_password(password: str, salt: Optional[str] = None) -> str:
    if not salt:
        salt = os.urandom(16).hex()
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return f"{salt}${pwd_hash}"

def verify_password(stored_password: str, password_attempt: str) -> bool:
    try:
        salt, pwd_hash = stored_password.split("$")
        check_hash = hashlib.pbkdf2_hmac("sha256", password_attempt.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
        return pwd_hash == check_hash
    except Exception:
        return False

@app.get("/")
async def serve_frontend():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    elif os.path.exists("templates/index.html"):
        return FileResponse("templates/index.html")
    raise HTTPException(status_code=404, detail="index.html not found")

@app.get("/api/leetcode-lookup")
async def leetcode_lookup(query: str):
    q = query.strip()
    if not q:
        raise HTTPException(status_code=400, detail="Problem title or number required")

    if q in LEETCODE_GLOBAL_CACHE:
        item = LEETCODE_GLOBAL_CACHE[q]
        return {"status": "success", "title": item["title"], "topic": item["topic"], "difficulty": item["difficulty"], "pattern": item["pattern"], "url": item["url"]}

    q_lower = q.lower()
    if q_lower in LEETCODE_GLOBAL_CACHE:
        item = LEETCODE_GLOBAL_CACHE[q_lower]
        return {"status": "success", "title": item["title"], "topic": item["topic"], "difficulty": item["difficulty"], "pattern": item["pattern"], "url": item["url"]}

    slug = q_lower.replace(" ", "-")
    try:
        query_payload = {
            "query": """
            query questionData($titleSlug: String!) {
              question(titleSlug: $titleSlug) {
                questionFrontendId
                title
                difficulty
                topicTags { name }
              }
            }
            """,
            "variables": {"titleSlug": slug}
        }
        req = urllib.request.Request(
            "https://leetcode.com/graphql",
            data=json.dumps(query_payload).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            res_data = json.loads(resp.read().decode())
            quest = res_data.get("data", {}).get("question")
            if quest:
                tags = [t["name"] for t in quest.get("topicTags", [])]
                main_topic = tags[0] if tags else "Algorithms"
                q_id = quest.get("questionFrontendId", "")
                full_title = f"#{q_id}. {quest['title']}" if q_id else quest['title']
                return {"status": "success", "title": full_title, "topic": main_topic, "difficulty": quest["difficulty"], "pattern": main_topic, "url": f"https://leetcode.com/problems/{slug}/"}
    except Exception:
        pass

    formatted_title = f"#{q}. Problem {q}" if q.isdigit() else q.replace("-", " ").title()
    return {"status": "success", "title": formatted_title, "topic": "Algorithms", "difficulty": "Medium", "pattern": "LeetCode Direct", "url": f"https://leetcode.com/problems/{slug}/"}

@app.get("/profile/")
def get_profile(username: Optional[str] = Query(None), db: Session = Depends(get_db)):
    prof = None
    if username:
        prof = db.query(models.UserProfile).filter(models.UserProfile.username == username).first()
    if not prof:
        prof = db.query(models.UserProfile).order_by(models.UserProfile.id.desc()).first()
    if not prof:
        prof = models.UserProfile(
            username="candidate",
            hashed_password=hash_password("admin123"),
            name="Keshav Gupta",
            solved_count=20,
            target_role="Software Development Engineer",
            primary_language="C++",
            experience_level="Beginner",
            phone_number="Verified"
        )
        db.add(prof)
        db.commit()
        db.refresh(prof)

    return {
        "id": prof.id,
        "name": prof.name,
        "username": prof.username,
        "solved_count": prof.solved_count,
        "target_role": prof.target_role,
        "primary_language": prof.primary_language,
        "experience_level": prof.experience_level,
        "phone_number": getattr(prof, "phone_number", "Verified") or "Verified"
    }

@app.post("/auth/login")
def login(creds: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.UserProfile).filter(models.UserProfile.username == creds.username).first()
    if not user or not verify_password(user.hashed_password, creds.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": "Success", "username": user.username, "name": user.name}

@app.post("/auth/register")
def register(user_data: dict, db: Session = Depends(get_db)):
    username = user_data.get("username", "").strip()
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")

    existing = db.query(models.UserProfile).filter(models.UserProfile.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already claimed")
    
    new_user = models.UserProfile(
        username=username,
        hashed_password=hash_password(user_data.get("password", "defaultpass")),
        name=user_data.get("name", "Candidate"),
        phone_number=user_data.get("phone_number", ""),
        primary_language=user_data.get("primary_language", "C++"),
        solved_count=int(user_data.get("solved_count", 0)),
        target_role=user_data.get("target_role", "Software Development Engineer")
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "Account registered securely", "username": new_user.username, "name": new_user.name}

@app.get("/streak/calculate/")
def get_streak(db: Session = Depends(get_db)):
    records = db.query(models.Problem.solved_date).distinct().order_by(models.Problem.solved_date.desc()).all()
    dates = [r[0] for r in records if r[0]]
    if not dates:
        return {"current_streak": 0}

    streak = 0
    today = date.today()
    check_date = today if today in dates else today - timedelta(days=1)

    while check_date in dates:
        streak += 1
        check_date -= timedelta(days=1)

    return {"current_streak": streak}

@app.get("/calendar/activity/")
def get_calendar_activity(db: Session = Depends(get_db)):
    records = db.query(models.Problem.solved_date, func.count(models.Problem.id)).group_by(models.Problem.solved_date).all()
    return {str(d): count for d, count in records if d}

@app.get("/target/")
def get_target(db: Session = Depends(get_db)):
    today = date.today()
    target = db.query(models.DailyTarget).filter(models.DailyTarget.target_date == today).first()
    if not target:
        target = models.DailyTarget(target_date=today, target_count=3, completed_count=0)
        db.add(target)
        db.commit()
        db.refresh(target)
    
    solved_today = db.query(models.Problem).filter(models.Problem.solved_date == today).count()
    target.completed_count = solved_today
    db.commit()
    return {"target_count": target.target_count, "completed_count": target.completed_count}

RESERVOIR = [
    {"title": "#1. Two Sum", "topic": "Arrays & Hashing", "difficulty": "Easy", "platform": "LeetCode", "url": "https://leetcode.com/problems/two-sum", "pattern": "Two Pointers"},
    {"title": "#20. Valid Parentheses", "topic": "Stacks", "difficulty": "Easy", "platform": "LeetCode", "url": "https://leetcode.com/problems/valid-parentheses", "pattern": "Monotonic Stack"},
    {"title": "#206. Reverse Linked List", "topic": "Linked Lists", "difficulty": "Easy", "platform": "LeetCode", "url": "https://leetcode.com/problems/reverse-linked-list", "pattern": "Two Pointers"},
    {"title": "#704. Binary Search", "topic": "Binary Search", "difficulty": "Easy", "platform": "LeetCode", "url": "https://leetcode.com/problems/binary-search", "pattern": "Binary Search"}
]

@app.get("/recommendations/")
def get_recommendations(pattern: Optional[str] = None):
    return RESERVOIR[:4]

@app.get("/discover/random")
def get_random_challenge():
    import random
    return random.choice(RESERVOIR)

@app.get("/problems/")
def get_problems(solved_date: Optional[str] = None, pattern: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.Problem)
    if solved_date:
        query = query.filter(models.Problem.solved_date == solved_date)
    if pattern and pattern != "ALL":
        query = query.filter(models.Problem.pattern_tag == pattern)
    
    probs = query.order_by(models.Problem.id.desc()).all()
    # Explicit dictionary serialization to ensure code columns return accurately
    return [
        {
            "id": p.id,
            "title": p.title,
            "topic": p.topic,
            "difficulty": p.difficulty,
            "platform": p.platform,
            "problem_url": p.problem_url,
            "notes": p.notes,
            "code_cpp": p.code_cpp or "",
            "code_python": p.code_python or "",
            "code_java": p.code_java or "",
            "pattern_tag": p.pattern_tag,
            "solved_date": str(p.solved_date),
            "next_review_date": str(p.next_review_date),
            "revision_count": p.revision_count
        } for p in probs
    ]

@app.get("/problems/due-today/")
def get_due_problems(db: Session = Depends(get_db)):
    today = date.today()
    probs = db.query(models.Problem).filter(models.Problem.next_review_date <= today).all()
    return [
        {
            "id": p.id,
            "title": p.title,
            "topic": p.topic,
            "difficulty": p.difficulty,
            "platform": p.platform,
            "problem_url": p.problem_url,
            "notes": p.notes,
            "code_cpp": p.code_cpp or "",
            "code_python": p.code_python or "",
            "code_java": p.code_java or "",
            "pattern_tag": p.pattern_tag,
            "solved_date": str(p.solved_date),
            "next_review_date": str(p.next_review_date),
            "revision_count": p.revision_count
        } for p in probs
    ]

@app.post("/problems/")
def add_problem(problem: dict, db: Session = Depends(get_db)):
    today = date.today()
    new_prob = models.Problem(
        title=problem.get("title"),
        platform="LeetCode",
        topic=problem.get("topic", "Algorithms"),
        difficulty=problem.get("difficulty", "Medium"),
        problem_url=problem.get("problem_url"),
        notes=problem.get("notes"),
        code_cpp=problem.get("code_cpp", ""),
        code_python=problem.get("code_python", ""),
        code_java=problem.get("code_java", ""),
        pattern_tag=problem.get("pattern_tag", "General"),
        solved_date=today,
        next_review_date=today + timedelta(days=1),
        revision_count=0
    )
    db.add(new_prob)
    db.commit()
    db.refresh(new_prob)
    return {"message": "Success", "id": new_prob.id}

# Multi-Language Code Update Endpoint
@app.put("/problems/{problem_id}/code")
def update_problem_code(problem_id: int, payload: dict, db: Session = Depends(get_db)):
    prob = db.query(models.Problem).filter(models.Problem.id == problem_id).first()
    if not prob:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    lang = payload.get("language", "cpp").lower()
    code = payload.get("code", "")

    if lang == "cpp":
        prob.code_cpp = code
    elif lang == "python":
        prob.code_python = code
    elif lang == "java":
        prob.code_java = code

    db.commit()
    return {"message": f"{lang.upper()} code committed to datastore"}

@app.put("/problems/{problem_id}/revise")
def mark_revised(problem_id: int, db: Session = Depends(get_db)):
    prob = db.query(models.Problem).filter(models.Problem.id == problem_id).first()
    if not prob:
        raise HTTPException(status_code=404, detail="Problem not found")
    stages = [1, 3, 7, 14, 30]
    next_step = prob.revision_count + 1
    interval = stages[min(next_step, len(stages) - 1)]
    prob.revision_count = next_step
    prob.next_review_date = date.today() + timedelta(days=interval)
    db.commit()
    return {"message": "Revised successfully"}

@app.delete("/problems/{problem_id}")
def delete_problem(problem_id: int, db: Session = Depends(get_db)):
    prob = db.query(models.Problem).filter(models.Problem.id == problem_id).first()
    if not prob:
        raise HTTPException(status_code=404, detail="Problem not found")
    db.delete(prob)
    db.commit()
    return {"message": "Deleted"}

@app.delete("/problems/all/purge")
def purge_all(db: Session = Depends(get_db)):
    db.query(models.Problem).delete()
    db.commit()
    return {"message": "Purged all"}