from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from auth_middleware import verify_token
import psycopg2
from psycopg2 import pool
import os
import time

app = FastAPI()

# =========================
# 🔹 DB CONFIG CHECK
# =========================
REQUIRED_ENV_VARS = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASS"]
for var in REQUIRED_ENV_VARS:
    if var not in os.environ:
        raise Exception(f"Missing required environment variable: {var}")

DB_CONFIG = {
    "host": os.environ["DB_HOST"],
    "database": os.environ["DB_NAME"],
    "user": os.environ["DB_USER"],
    "password": os.environ["DB_PASS"]
}

# =========================
# 🔹 CONNECTION POOL
# =========================
def create_pool():
    retries = 10
    for attempt in range(retries):
        try:
            p = pool.SimpleConnectionPool(1, 10, **DB_CONFIG)
            print("✅ User DB connection pool created")
            return p
        except Exception as e:
            print(f"❌ Pool failed (attempt {attempt+1}/{retries}): {e}")
            time.sleep(2)
    raise Exception("User Database pool not reachable")

connection_pool = create_pool()

def get_db():
    conn = connection_pool.getconn()
    try:
        yield conn
    finally:
        connection_pool.putconn(conn)

class UserCreate(BaseModel):
    username: str 

@app.on_event("startup")
def startup():
    print("User Service starting... Schema managed by InitContainer.")

# =========================
# 🔹 ENDPOINTS
# =========================

@app.get("/health")
def health():
    return {"status": "ok"}

# Endpoint for Auth Service to sync new users (No JWT required)
@app.post("/users")
def create_user(user_data: UserCreate, conn=Depends(get_db)):
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username) VALUES (%s) ON CONFLICT (username) DO NOTHING RETURNING id",
            (user_data.username,)
        )
        result = cur.fetchone()
        conn.commit()
        
        if result:
            user_id = int(result[0])
            print(f"✅ User Sync: Created {user_data.username}")
            return {"id": user_id, "username": user_data.username}
        else:
            return {"message": "User already exists", "username": user_data.username}
            
    except Exception as e:
        conn.rollback()
        print(f"CREATE USER ERROR: {e}")
        raise HTTPException(status_code=500, detail="Database write failed")
    finally:
        cur.close()

# Protected endpoint for UI/Client retrieval
@app.get("/users")
def get_users(user=Depends(verify_token), conn=Depends(get_db)):
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, username FROM users")
        rows = cur.fetchall()
        return [{"id": int(r[0]), "username": r[1]} for r in rows]
    except Exception as e:
        print(f"FETCH USERS ERROR: {e}")
        raise HTTPException(status_code=500, detail="Database read failed")
    finally:
        cur.close()