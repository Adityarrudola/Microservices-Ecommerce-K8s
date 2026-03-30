from fastapi import FastAPI, HTTPException
from fastapi import Depends
from auth_middleware import verify_token
import psycopg2
import os
import requests
import time

app = FastAPI()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "postgres"),
    "database": os.getenv("DB_NAME", "order_db"),
    "user": os.getenv("DB_USER", "admin"),
    "password": os.getenv("DB_PASS", "admin")
}

USER_SERVICE = "http://user-service"
PRODUCT_SERVICE = "http://product-service"


def get_connection():
    for _ in range(5):
        try:
            return psycopg2.connect(**DB_CONFIG)
        except:
            time.sleep(2)
    raise Exception("DB not reachable")


# init table
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        user_id INT,
        product_id INT
    )
    """)

    conn.commit()
    cur.close()
    conn.close()


init_db()


@app.post("/orders")
def create_order(order: dict, user=Depends(verify_token)):
    user_id = order["user_id"]
    product_id = order["product_id"]

    # 🔥 Call user service
    user_res = requests.get(f"{USER_SERVICE}/users")
    users = user_res.json()

    if not any(u["id"] == user_id for u in users):
        raise HTTPException(status_code=400, detail="User not found")

    # 🔥 Call product service
    product_res = requests.get(f"{PRODUCT_SERVICE}/products")
    products = product_res.json()

    if not any(p["id"] == product_id for p in products):
        raise HTTPException(status_code=400, detail="Product not found")

    # save order
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO orders (user_id, product_id) VALUES (%s, %s) RETURNING id",
        (user_id, product_id)
    )

    order_id = cur.fetchone()[0]
    conn.commit()

    cur.close()
    conn.close()

    return {
        "order_id": order_id,
        "user_id": user_id,
        "product_id": product_id
    }


@app.get("/orders")
def get_orders(user=Depends(verify_token)):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM orders")
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [
        {"id": r[0], "user_id": r[1], "product_id": r[2]}
        for r in rows
    ]