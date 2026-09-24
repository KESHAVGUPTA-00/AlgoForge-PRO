# ⚡ AlgoForge Pro Enterprise
> **Autonomous DSA Intelligence, Retention & Spaced Repetition Platform**

Architected & Developed by **Keshav Gupta**  
*Protected under Proprietary License &copy; 2026. All Rights Reserved.*

---

## 📌 Problem Statement
Most engineering students solve hundreds of algorithmic problems on platforms like LeetCode and Codeforces, but suffer from significant cognitive retention decay before technical interviews. **AlgoForge Pro** solves this by enforcing an automated mathematical **Spaced Repetition Revision Cycle**, candidate activity heatmaps, and verified recruitment dossiers.

---

## 🚀 Key Engineering Highlights

- **🧠 Automated Spaced Repetition Engine:** Dynamically calculates review intervals based on mastery stages ($1 \rightarrow 3 \rightarrow 7 \rightarrow 14 \rightarrow 30$ days).
- **🔒 Zero-Dependency Cryptographic Vault:** Replaced brittle third-party libraries with native `hashlib.pbkdf2_hmac` (SHA-256 with 100,000 iterations and unique salts) and `secrets.compare_digest` to prevent timing attacks.
- **📅 Real-Time Execution Calendar:** High-performance database aggregation (`GROUP BY solved_date`) to render monthly activity heatmaps with single-click date filtering.
- **📜 Verified Recruitment Dossier & Dynamic QR Engine:** Client-side dynamic QR generation (`qrcode.js`) encoding verified candidate stats, primary language, and mastery distribution.
- **✨ Built-in AI Copilot Hook:** Integrated Google Gemini assistant queries to break down optimal time/space complexity intuitions in C++, Java, Python, or JavaScript.

---

## 🛠️ System Architecture & Tech Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | FastAPI (Python) | High-performance asynchronous REST endpoints |
| **Database & ORM** | SQLite + SQLAlchemy | Relational datastore with indexed lookups |
| **Security Layer** | PBKDF2-HMAC-SHA256 | Native salted credential hashing |
| **Frontend UI** | Tailwind CSS + Jinja2 | Responsive dark-mode enterprise interface |
| **Data Visualization**| Chart.js | Interactive problem difficulty doughnut charts |
| **Verification** | QRCode.js | Dynamic cryptographic verification seals |

---

## 💻 Local Setup & Installation

```bash
# 1. Clone the repository
git clone [https://github.com/KESHAVGUPTA-00/AlgoForge-PRO.git](https://github.com/KESHAVGUPTA-00/AlgoForge-PRO.git)
cd AlgoForge-PRO

# 2. Install dependencies
pip install fastapi uvicorn sqlalchemy pydantic jinja2

# 3. Start the server
uvicorn main:app --reload
