from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from auth_middleware import verify_token
import psycopg2
import os
import time

app = FastAPI()


# ---------------- CONFIG ----------------
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


# ---------------- REQUEST SCHEMA ----------------
class ProductRequest(BaseModel):
    name: str
    price: int


# ---------------- DB CONNECTION ----------------
def get_connection():
    retries = 10
    delay = 2

    for attempt in range(retries):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            print("Connected to Product DB")
            return conn
        except Exception as e:
            print(f"Product DB connection failed (attempt {attempt+1}/{retries}): {e}")
            time.sleep(delay)

    raise Exception("Product DB not reachable after retries")


# ---------------- INIT DB ----------------
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            price INT NOT NULL
        )
        """)
        conn.commit()
        print("Products table initialized successfully")
    finally:
        cur.close()
        conn.close()


@app.on_event("startup")
def startup_event():
    init_db()


# ---------------- CREATE PRODUCT ----------------
@app.post("/products")
def create_product(product: ProductRequest, user=Depends(verify_token)):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO products (name, price) VALUES (%s, %s) RETURNING id",
            (product.name, product.price)
        )
        # Explicitly fetch as int
        product_id = int(cur.fetchone()[0])
        conn.commit()

        return {
            "id": product_id,
            "name": product.name,
            "price": product.price
        }

    except Exception as e:
        conn.rollback()
        print(f"CREATE PRODUCT ERROR: {e}")
        raise HTTPException(status_code=500, detail="Failed to create product")

    finally:
        cur.close()
        conn.close()


# ---------------- GET PRODUCTS ----------------
@app.get("/products")
def get_products(user=Depends(verify_token)):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT id, name, price FROM products")
        rows = cur.fetchall()

        # Ensure IDs are returned as integers for order-service validation
        return [
            {"id": int(r[0]), "name": r[1], "price": r[2]}
            for r in rows
        ]

    except Exception as e:
        print(f"FETCH PRODUCTS ERROR: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch products")

    finally:
        cur.close()
        conn.close()