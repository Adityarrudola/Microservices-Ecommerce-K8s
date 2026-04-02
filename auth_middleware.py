from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from auth_middleware import verify_token
import psycopg2
from psycopg2 import pool
import os
import time

app = FastAPI()


# =========================
# CONFIG (STRICT ENV CHECK)
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
# CONNECTION POOL (WITH RETRY)
# =========================
def create_pool():
    retries = 10
    delay = 2

    for attempt in range(retries):
        try:
            pool_instance = pool.SimpleConnectionPool(1, 10, **DB_CONFIG)
            print("Connection pool created")
            return pool_instance
        except Exception as e:
            print(f"Pool creation failed (attempt {attempt+1}/{retries}): {e}")
            time.sleep(delay)

    raise Exception("Database pool not reachable after retries")


connection_pool = create_pool()


# =========================
# DB DEPENDENCY
# =========================
def get_db():
    conn = connection_pool.getconn()
    try:
        yield conn
    finally:
        connection_pool.putconn(conn)


# =========================
# REQUEST SCHEMA
# =========================
class UserCreate(BaseModel):
    name: str


# =========================
# STARTUP EVENT (INIT TABLE)
# =========================
@app.on_event("startup")
def startup():
    conn = connection_pool.getconn()
    cur = conn.cursor()

    try:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL
        )
        """)
        conn.commit()
        print("Users table initialized")
    finally:
        cur.close()
        connection_pool.putconn(conn)


# =========================
# HEALTH CHECK (FOR K8s)
# =========================
@app.get("/health")
def health():
    return {"status": "ok"}


# =========================
# CREATE USER
# =========================
@app.post("/users")
def create_user(
    user_data: UserCreate,
    user=Depends(verify_token),
    conn=Depends(get_db)
):
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO users (name) VALUES (%s) RETURNING id",
            (user_data.name,)
        )
        user_id = cur.fetchone()[0]
        conn.commit()

        return {
            "id": user_id,
            "name": user_data.name
        }

    except Exception as e:
        conn.rollback()
        print("CREATE USER ERROR:", e)
        raise HTTPException(status_code=500, detail="Failed to create user")

    finally:
        cur.close()


# =========================
# GET USERS
# =========================
@app.get("/users")
def get_users(
    user=Depends(verify_token),
    conn=Depends(get_db)
):
    cur = conn.cursor()

    try:
        cur.execute("SELECT id, name FROM users")
        rows = cur.fetchall()

        return [{"id": r[0], "name": r[1]} for r in rows]

    except Exception as e:
        print("FETCH USERS ERROR:", e)
        raise HTTPException(status_code=500, detail="Failed to fetch users")

    finally:
        cur.close()