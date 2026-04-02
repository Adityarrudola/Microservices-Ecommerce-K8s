from fastapi import FastAPI, HTTPException, Header
import psycopg2
import os
import jwt
import datetime
import time

app = FastAPI()

SECRET_KEY = os.getenv("SECRET_KEY", "mysecretkey")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "postgres"),
    "database": os.getenv("DB_NAME", "auth_db"),
    "user": os.getenv("DB_USER", "admin"),
    "password": os.getenv("DB_PASS", "admin")
}


# ---------------- DB CONNECTION ----------------
def get_connection():
    for _ in range(5):
        try:
            return psycopg2.connect(**DB_CONFIG)
        except:
            time.sleep(2)
    raise Exception("DB not reachable")


# ---------------- INIT DB ----------------
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    conn.commit()
    cur.close()
    conn.close()


init_db()


# ---------------- TOKEN GENERATION ----------------
def generate_token(user_id, username):
    payload = {
        "sub": username,
        "user_id": user_id,   # 🔥 IMPORTANT FIX
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


# ---------------- REGISTER ----------------
@app.post("/register")
def register(user: dict):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (user["username"], user["password"])
        )
        conn.commit()
    except Exception as e:
        print("REGISTER ERROR:", e)
        raise HTTPException(status_code=400, detail="User already exists")

    cur.close()
    conn.close()

    return {"message": "User registered"}


# ---------------- LOGIN ----------------
@app.post("/login")
def login(user: dict):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, username FROM users WHERE username=%s AND password=%s",
        (user["username"], user["password"])
    )

    result = cur.fetchone()

    cur.close()
    conn.close()

    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_id, username = result

    token = generate_token(user_id, username)

    return {
        "token": token,
        "user_id": user_id,
        "username": username
    }


# ---------------- VALIDATE TOKEN ----------------
@app.get("/validate")
def validate_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing token")

    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

        return {
            "username": payload["sub"],
            "user_id": payload["user_id"]   # 🔥 IMPORTANT FIX
        }

    except Exception as e:
        print("JWT ERROR:", e)
        raise HTTPException(status_code=401, detail="Invalid or expired token")