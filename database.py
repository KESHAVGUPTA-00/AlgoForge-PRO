# ==============================================================================
# Project: AlgoForge Pro Enterprise
# Author & Copyright Owner: Keshav Gupta (c) 2026
# All Rights Reserved. Unauthorized copying, distribution, or claiming authorship
# of this software architecture is strictly prohibited by copyright law.
# ==============================================================================
# ==============================================================================
# Project: AlgoForge Pro Enterprise
# Author: Keshav Gupta (c) 2026
# ==============================================================================
# ==============================================================================
# Project: AlgoForge Pro Enterprise
# Author: Keshav Gupta (c) 2026
# ==============================================================================
import os
import urllib.parse
from motor.motor_asyncio import AsyncIOMotorClient

# Yahan apna username aur password alag-alag variable me rakho
DB_USER = "keshav99"
# Apna naya password yahan quotes ke andar likho:
RAW_PASSWORD = "Keshav2007"  # Replace with your actual password

# Special characters ko safely escape/encode karega
ESCAPED_PASSWORD = urllib.parse.quote_plus(RAW_PASSWORD)

# Cluster URL safe string
DEFAULT_URI = f"mongodb+srv://{DB_USER}:{ESCAPED_PASSWORD}@cluster0.kserwpm.mongodb.net/?appName=Cluster0"

MONGO_URI = os.getenv("MONGO_URI", DEFAULT_URI)

client = AsyncIOMotorClient(MONGO_URI)
db = client["algoforge_prod_db"]

# Persistent Collections
users_collection = db["users"]
problems_collection = db["problems"]
daily_targets_collection = db["daily_targets"]