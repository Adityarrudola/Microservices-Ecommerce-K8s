from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
import psycopg2
import os
import jwt
import requests
from datetime import datetime, timedelta, timezone
import time

app = FastAPI()

# ---------------- CONFIG ----------------
# We check for all required variables including the Secret Key and DB info
REQUIRED_ENV_VARS = ["SECRET_KEY", "DB_HOST", "DB_NAME", "DB_USER", "DB_PASS"]

for var in REQUIRED_ENV_VARS:
    if var not in os.environ:
        raise Exception(f"Missing required environment variable: {var}")

SECRET_KEY = os.environ["SECRET_KEY"]

# Service-to-Service communication URL (Internal K8s DNS)
# Defaults to localhost if not set (for local dev), but uses K8s service in production
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:80").rstrip("/")

DB_CONFIG = {
    "host": os.environ["DB_HOST"],
    "database": os.environ["DB_NAME"],
    "user": os.environ["DB_USER"],
    "password": os.environ["DB_PASS"]
}

# ---------------- REQUEST SCHEMA ----------------
class UserRequest(BaseModel):
    username: str
    password: str

# ---------------- DB CONNECTION ----------------
def get_connection():
    retries = 10
    delay = 2
    for attempt in range(retries):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            return conn
        except Exception as e:
            print(f"Auth DB connection failed (attempt {attempt+1}/{retries}): {e}")
            time.sleep(delay)
    raise Exception("Auth DB not reachable after retries")

# ---------------- INIT DB ----------------
def init_db():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """)
        conn.commit()
        print("Auth Database initialized successfully")
    finally:
        cur.close()
        conn.close()

@app.on_event("startup")
def startup_event():
    init_db()

# ---------------- TOKEN GENERATION ----------------
def generate_token(user_id: int, username: str) -> str:
    payload = {
        "sub": username,
        "user_id": int(user_id), 
        "exp": datetime.now(timezone.utc) + timedelta(hours=2)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# ---------------- REGISTER ----------------
@app.post("/register")
def register(user: UserRequest):
    conn = get_connection()
    cur = conn.cursor()
    try:
        # 1. Save credentials to Auth Database
        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id",
            (user.username, user.password)
        )
        user_id = cur.fetchone()[0]
        conn.commit()

        # 2. 🚀 THE SYNC HANDSHAKE
        # Inform the User Service that a new user profile needs to be created
        try:
            sync_response = requests.post(
                f"{USER_SERVICE_URL}/users",
                json={"username": user.username},
                timeout=5
            )
            if sync_response.status_code != 200:
                print(f"⚠️ Sync Warning: User Service at {USER_SERVICE_URL} returned {sync_response.status_code}")
                print(f"Response text: {sync_response.text}")
            else:
                print(f"✅ Successfully synced user {user.username} to User Service")
        except Exception as e:
            # We catch this so a networking error doesn't break the registration flow,
            # but we log it clearly for debugging.
            print(f"❌ Sync Error: Could not reach User Service at {USER_SERVICE_URL}: {e}")

        return {"message": "User registered successfully", "user_id": user_id}

    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        raise HTTPException(status_code=400, detail="User already exists")
    except Exception as e:
        conn.rollback()
        print("REGISTER ERROR:", e)
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        cur.close()
        conn.close()

# ---------------- LOGIN ----------------
@app.post("/login")
def login(user: UserRequest):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id, username FROM users WHERE username=%s AND password=%s",
            (user.username, user.password)
        )
        result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        user_id, username = result
        token = generate_token(user_id, username)
        return {"token": token, "user_id": user_id, "username": username}
    finally:
        cur.close()
        conn.close()

# ---------------- VALIDATE TOKEN ----------------
@app.get("/validate")
def validate_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    try:
        token = authorization.replace("Bearer ", "").strip()
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return {"username": payload["sub"], "user_id": int(payload["user_id"])}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        print("VALIDATION ERROR:", e)
        raise HTTPException(status_code=500, detail="Internal server error")