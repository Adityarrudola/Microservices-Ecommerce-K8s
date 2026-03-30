from fastapi import FastAPI
from fastapi import Depends
from auth_middleware import verify_token
import psycopg2
import os


app = FastAPI()

# env variables (IMPORTANT)
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_NAME = os.getenv("DB_NAME", "product_db")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASS = os.getenv("DB_PASS", "admin")

conn = psycopg2.connect(
    host=DB_HOST,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASS
)

cur = conn.cursor()

# create table
cur.execute("""
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name TEXT,
    price INT
)
""")
conn.commit()


@app.post("/products")
def create_product(product: dict, user=Depends(verify_token)):
    cur.execute(
        "INSERT INTO products (name, price) VALUES (%s, %s) RETURNING id",
        (product["name"], product["price"])
    )
    product_id = cur.fetchone()[0]
    conn.commit()
    return {"id": product_id, **product}


@app.get("/products")
def get_products(user=Depends(verify_token)):
    cur.execute("SELECT * FROM products")
    rows = cur.fetchall()
    return [
        {"id": r[0], "name": r[1], "price": r[2]}
        for r in rows
    ]