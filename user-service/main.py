from fastapi import FastAPI
from fastapi import Depends
from auth_middleware import verify_token
import psycopg2
import os


app = FastAPI()

conn = psycopg2.connect(
    host="postgres",
    database="user_db",
    user="admin",
    password="admin"
)

cur = conn.cursor()

# create table
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name TEXT
)
""")
conn.commit()


@app.post("/users")
def create_user(user_data: dict, user=Depends(verify_token)):
    cur.execute("INSERT INTO users (name) VALUES (%s) RETURNING id", (user["name"],))
    user_id = cur.fetchone()[0]
    conn.commit()
    return {"id": user_id, "name": user["name"]}


@app.get("/users")
def get_users(user=Depends(verify_token)):
    cur.execute("SELECT * FROM users")
    rows = cur.fetchall()
    return [{"id": r[0], "name": r[1]} for r in rows]