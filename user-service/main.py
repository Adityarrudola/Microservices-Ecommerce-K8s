from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from auth_middleware import verify_token
import psycopg2
from psycopg2 import pool
import os

app = FastAPI()

# =========================
# 🔹 DB CONFIG (ENV BASED)
# =========================
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "postgres"),
    "database": os.getenv("DB_NAME", "user_db"),
    "user": os.getenv("DB_USER", "admin"),
    "password": os.getenv("DB_PASSWORD", "admin"),
}

# =========================
# 🔹 CONNECTION POOL
# =========================
try:
    connection_pool = pool.SimpleConnectionPool(1, 10, **DB_CONFIG)
except Exception as e:
    raise Exception(f"Database connection failed: {e}")

# =========================
# 🔹 DB DEPENDENCY
# =========================
def get_db():
    conn = connection_pool.getconn()
    try:
        yield conn
    finally:
        connection_pool.putconn(conn)

# =========================
# 🔹 PYDANTIC MODEL
# =========================
class UserCreate(BaseModel):
    name: str

# =========================
# 🔹 STARTUP EVENT (TABLE)
# =========================
@app.on_event("startup")
def startup():
    conn = connection_pool.getconn()
    try:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT
        )
        """)
        conn.commit()
    finally:
        connection_pool.putconn(conn)

# =========================
# 🔹 HEALTH CHECK (K8s)
# =========================
@app.get("/health")
def health():
    return {"status": "ok"}

# =========================
# 🔹 CREATE USER
# =========================
@app.post("/users")
def create_user(
    user_data: UserCreate,
    user=Depends(verify_token),
    conn=Depends(get_db)
):
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (name) VALUES (%s) RETURNING id",
            (user_data.name,)
        )
        user_id = cur.fetchone()[0]
        conn.commit()

        return {"id": user_id, "name": user_data.name}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# =========================
# 🔹 GET USERS
# =========================
@app.get("/users")
def get_users(
    user=Depends(verify_token),
    conn=Depends(get_db)
):
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users")
        rows = cur.fetchall()

        return [{"id": r[0], "name": r[1]} for r in rows]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))