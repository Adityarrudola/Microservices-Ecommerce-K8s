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


def get_connection():
    for _ in range(5):
        try:
            return psycopg2.connect(**DB_CONFIG)
        except:
            time.sleep(2)
    raise Exception("DB not reachable")


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


def generate_token(username):
    payload = {
        "sub": username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


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
    except:
        raise HTTPException(status_code=400, detail="User already exists")

    cur.close()
    conn.close()

    return {"message": "User registered"}


@app.post("/login")
def login(user: dict):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM users WHERE username=%s AND password=%s",
        (user["username"], user["password"])
    )

    result = cur.fetchone()

    cur.close()
    conn.close()

    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = generate_token(user["username"])
    return {"token": token}

@app.get("/validate")
def validate_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing token")

    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return {"username": payload["sub"]}
    except Exception as e:
        print("JWT ERROR:", e)   # 🔥 important for debugging
        raise HTTPException(status_code=401, detail="Invalid or expired token")