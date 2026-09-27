# ==============================================================================
# Project: AlgoForge Pro Enterprise (MongoDB Atlas Edition)
# Author & Copyright Owner: Keshav Gupta (c) 2026
# All Rights Reserved.
# ==============================================================================
import os
import hashlib
import json
import urllib.request
from datetime import date, timedelta
from typing import Optional
from bson import ObjectId
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse

from database import users_collection, problems_collection, daily_targets_collection

app = FastAPI(title="AlgoForge Pro Enterprise - MongoDB Live")

LEETCODE_GLOBAL_CACHE = {}

def sync_all_leetcode_questions():
    global LEETCODE_GLOBAL_CACHE
    try:
        url = "https://leetcode.com/api/problems/all/"
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
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
    except Exception as e:
        print(f"LeetCode live sync notice: {e}")

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
        with urllib.request.urlopen(req, timeout=4) as resp:
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
async def get_profile(username: Optional[str] = Query(None)):
    if not username:
        return {
            "authenticated": False,
            "name": "Guest Candidate",
            "username": "guest",
            "solved_count": 0,
            "target_role": "Sign In to Unlock Workspace",
            "primary_language": "--",
            "experience_level": "Unauthenticated",
            "phone_number": "Not Registered"
        }

    user = await users_collection.find_one({"username": username})
    if not user:
        return {
            "authenticated": False,
            "name": "Guest Candidate",
            "username": "guest",
            "solved_count": 0,
            "target_role": "Sign In to Unlock Workspace",
            "primary_language": "--",
            "experience_level": "Unauthenticated",
            "phone_number": "Not Registered"
        }

    return {
        "authenticated": True,
        "name": user.get("name", "Candidate"),
        "username": user.get("username"),
        "solved_count": user.get("solved_count", 0),
        "target_role": user.get("target_role", "Software Development Engineer"),
        "primary_language": user.get("primary_language", "C++"),
        "experience_level": user.get("experience_level", "Verified Candidate"),
        "phone_number": user.get("phone_number", "Verified")
    }

@app.post("/auth/login")
async def login(creds: dict):
    username = creds.get("username")
    password = creds.get("password")
    user = await users_collection.find_one({"username": username})
    if not user or not verify_password(user.get("hashed_password", ""), password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"message": "Success", "username": user["username"], "name": user["name"]}

@app.post("/auth/register")
async def register(user_data: dict):
    username = user_data.get("username", "").strip()
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")

    existing = await users_collection.find_one({"username": username})
    if existing:
        raise HTTPException(status_code=400, detail="Username is already claimed")

    doc = {
        "username": username,
        "hashed_password": hash_password(user_data.get("password", "defaultpass")),
        "name": user_data.get("name", "Candidate"),
        "phone_number": user_data.get("phone_number", ""),
        "primary_language": user_data.get("primary_language", "C++"),
        "solved_count": int(user_data.get("solved_count", 0)),
        "target_role": user_data.get("target_role", "Software Development Engineer"),
        "experience_level": "Verified Candidate"
    }
    await users_collection.insert_one(doc)
    return {"message": "Account created successfully", "username": username, "name": doc["name"]}

@app.get("/streak/calculate/")
async def get_streak():
    cursor = problems_collection.find({}, {"solved_date": 1})
    dates = set()
    async for doc in cursor:
        if doc.get("solved_date"):
            dates.add(doc["solved_date"])

    if not dates:
        return {"current_streak": 0}

    streak = 0
    today = str(date.today())
    yesterday = str(date.today() - timedelta(days=1))
    check_date = date.today() if today in dates else date.today() - timedelta(days=1)

    while str(check_date) in dates:
        streak += 1
        check_date -= timedelta(days=1)

    return {"current_streak": streak}

@app.get("/calendar/activity/")
async def get_calendar_activity():
    cursor = problems_collection.find({}, {"solved_date": 1})
    activity = {}
    async for doc in cursor:
        d = doc.get("solved_date")
        if d:
            activity[d] = activity.get(d, 0) + 1
    return activity

@app.get("/target/")
async def get_target():
    today_str = str(date.today())
    target = await daily_targets_collection.find_one({"target_date": today_str})
    if not target:
        target = {"target_date": today_str, "target_count": 3, "completed_count": 0}
        await daily_targets_collection.insert_one(target)

    solved_today = await problems_collection.count_documents({"solved_date": today_str})
    await daily_targets_collection.update_one({"target_date": today_str}, {"$set": {"completed_count": solved_today}})
    return {"target_count": target.get("target_count", 3), "completed_count": solved_today}

@app.get("/problems/")
async def get_problems(solved_date: Optional[str] = None, pattern: Optional[str] = None):
    query = {}
    if solved_date:
        query["solved_date"] = solved_date
    if pattern and pattern != "ALL":
        query["pattern_tag"] = pattern

    cursor = problems_collection.find(query).sort("_id", -1)
    results = []
    async for p in cursor:
        results.append({
            "id": str(p["_id"]),
            "title": p.get("title"),
            "topic": p.get("topic"),
            "difficulty": p.get("difficulty"),
            "platform": p.get("platform", "LeetCode"),
            "problem_url": p.get("problem_url"),
            "notes": p.get("notes"),
            "code_cpp": p.get("code_cpp", ""),
            "code_python": p.get("code_python", ""),
            "code_java": p.get("code_java", ""),
            "pattern_tag": p.get("pattern_tag", "General"),
            "solved_date": p.get("solved_date"),
            "next_review_date": p.get("next_review_date"),
            "revision_count": p.get("revision_count", 0)
        })
    return results

@app.get("/problems/due-today/")
async def get_due_problems():
    today_str = str(date.today())
    cursor = problems_collection.find({"next_review_date": {"$lte": today_str}})
    results = []
    async for p in cursor:
        results.append({
            "id": str(p["_id"]),
            "title": p.get("title"),
            "topic": p.get("topic"),
            "difficulty": p.get("difficulty"),
            "platform": p.get("platform", "LeetCode"),
            "problem_url": p.get("problem_url"),
            "notes": p.get("notes"),
            "code_cpp": p.get("code_cpp", ""),
            "code_python": p.get("code_python", ""),
            "code_java": p.get("code_java", ""),
            "pattern_tag": p.get("pattern_tag", "General"),
            "solved_date": p.get("solved_date"),
            "next_review_date": p.get("next_review_date"),
            "revision_count": p.get("revision_count", 0)
        })
    return results

@app.post("/problems/")
async def add_problem(problem: dict):
    today = date.today()
    doc = {
        "title": problem.get("title"),
        "platform": "LeetCode",
        "topic": problem.get("topic", "Algorithms"),
        "difficulty": problem.get("difficulty", "Medium"),
        "problem_url": problem.get("problem_url"),
        "notes": problem.get("notes"),
        "code_cpp": problem.get("code_cpp", ""),
        "code_python": problem.get("code_python", ""),
        "code_java": problem.get("code_java", ""),
        "pattern_tag": problem.get("pattern_tag", "General"),
        "solved_date": str(today),
        "next_review_date": str(today + timedelta(days=1)),
        "revision_count": 0
    }
    result = await problems_collection.insert_one(doc)
    return {"message": "Success", "id": str(result.inserted_id)}

@app.put("/problems/{problem_id}/code")
async def update_problem_code(problem_id: str, payload: dict):
    try:
        oid = ObjectId(problem_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    lang = payload.get("language", "cpp").lower()
    code = payload.get("code", "")
    field = f"code_{lang}"
    await problems_collection.update_one({"_id": oid}, {"$set": {field: code}})
    return {"message": f"{lang.upper()} solution committed to MongoDB"}

@app.put("/problems/{problem_id}/revise")
async def mark_revised(problem_id: str):
    try:
        oid = ObjectId(problem_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    prob = await problems_collection.find_one({"_id": oid})
    if not prob:
        raise HTTPException(status_code=404, detail="Problem not found")

    stages = [1, 3, 7, 14, 30]
    next_step = prob.get("revision_count", 0) + 1
    interval = stages[min(next_step, len(stages) - 1)]
    next_review = str(date.today() + timedelta(days=interval))

    await problems_collection.update_one(
        {"_id": oid},
        {"$set": {"revision_count": next_step, "next_review_date": next_review}}
    )
    return {"message": "Revised successfully"}

@app.delete("/problems/{problem_id}")
async def delete_problem(problem_id: str):
    try:
        oid = ObjectId(problem_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    await problems_collection.delete_one({"_id": oid})
    return {"message": "Deleted"}

@app.delete("/problems/all/purge")
async def purge_all():
    await problems_collection.delete_many({})
    return {"message": "Purged all"}

BLIND75_DATABASE = [
    {"num": "1", "title": "Two Sum", "topic": "Arrays & Hashing", "difficulty": "Easy", "pattern": "Two Pointers"},
    {"num": "121", "title": "Best Time to Buy and Sell Stock", "topic": "Sliding Window", "difficulty": "Easy", "pattern": "Sliding Window"},
    {"num": "217", "title": "Contains Duplicate", "topic": "Arrays & Hashing", "difficulty": "Easy", "pattern": "Hashing"},
    {"num": "238", "title": "Product of Array Except Self", "topic": "Prefix Sum", "difficulty": "Medium", "pattern": "Arrays"},
    {"num": "53", "title": "Maximum Subarray", "topic": "Dynamic Programming", "difficulty": "Medium", "pattern": "Kadane's"},
    {"num": "15", "title": "3Sum", "topic": "Two Pointers", "difficulty": "Medium", "pattern": "Two Pointers"},
    {"num": "11", "title": "Container With Most Water", "topic": "Two Pointers", "difficulty": "Medium", "pattern": "Two Pointers"},
    {"num": "3", "title": "Longest Substring Without Repeating", "topic": "Sliding Window", "difficulty": "Medium", "pattern": "Sliding Window"},
    {"num": "20", "title": "Valid Parentheses", "topic": "Stacks", "difficulty": "Easy", "pattern": "Monotonic Stack"},
    {"num": "206", "title": "Reverse Linked List", "topic": "Linked Lists", "difficulty": "Easy", "pattern": "Two Pointers"},
    {"num": "141", "title": "Linked List Cycle", "topic": "Linked Lists", "difficulty": "Easy", "pattern": "Fast & Slow Pointers"},
    {"num": "21", "title": "Merge Two Sorted Lists", "topic": "Linked Lists", "difficulty": "Easy", "pattern": "Two Pointers"},
    {"num": "704", "title": "Binary Search", "topic": "Binary Search", "difficulty": "Easy", "pattern": "Binary Search"},
    {"num": "33", "title": "Search in Rotated Sorted Array", "topic": "Binary Search", "difficulty": "Medium", "pattern": "Binary Search"},
    {"num": "70", "title": "Climbing Stairs", "topic": "Dynamic Programming", "difficulty": "Easy", "pattern": "Dynamic Programming"},
    {"num": "198", "title": "House Robber", "topic": "Dynamic Programming", "difficulty": "Medium", "pattern": "Dynamic Programming"},
    {"num": "200", "title": "Number of Islands", "topic": "Graphs", "difficulty": "Medium", "pattern": "BFS/DFS"}
]

@app.get("/api/blind75")
async def get_blind75_status():
    cursor = problems_collection.find({}, {"title": 1})
    solved_titles = [doc.get("title", "").lower() async for doc in cursor]
    annotated = []
    completed_count = 0
    for item in BLIND75_DATABASE:
        is_done = any(item["title"].lower() in t or f"#{item['num']}." in t for t in solved_titles)
        if is_done:
            completed_count += 1
        annotated.append({**item, "completed": is_done})
    
    return {
        "total": len(BLIND75_DATABASE),
        "completed": completed_count,
        "percentage": round((completed_count / len(BLIND75_DATABASE)) * 100),
        "items": annotated
    }

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