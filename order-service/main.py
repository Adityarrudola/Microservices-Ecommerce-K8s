from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from auth_middleware import verify_token
import psycopg2
import os
import requests
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

# Internal K8s Service URLs
USER_SERVICE = os.getenv("USER_SERVICE_URL", "http://user-service:80").rstrip("/")
PRODUCT_SERVICE = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:80").rstrip("/")

# ---------------- REQUEST SCHEMA ----------------
class OrderRequest(BaseModel):
    product_id: int

# ---------------- DB CONNECTION ----------------
def get_connection():
    retries = 5
    for attempt in range(retries):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            return conn
        except Exception as e:
            print(f"Order DB connection failed (attempt {attempt+1}/{retries}): {e}")
            time.sleep(2)
    raise Exception("Order DB not reachable")

# ---------------- INIT DB ----------------
def init_db():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            user_id INT NOT NULL,
            product_id INT NOT NULL
        )
        """)
        conn.commit()
        print("Orders table initialized")
    finally:
        cur.close()
        conn.close()

@app.on_event("startup")
def startup_event():
    init_db()

# ---------------- SERVICE CALL HELPER ----------------
def call_service(url: str, authorization: str):
    try:
        print(f"Calling dependent service: {url}")
        response = requests.get(
            url,
            headers={"Authorization": authorization},
            timeout=5
        )
        return response
    except Exception as e:
        print(f"Connection Error to {url}: {e}")
        raise HTTPException(status_code=503, detail=f"Service at {url} unavailable")

# ---------------- CREATE ORDER ----------------
@app.post("/orders")
def create_order(
    order: OrderRequest,
    authorization: str = Header(None),
    user=Depends(verify_token)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Auth Header")

    # 1. EXTRACT USER ID FROM TOKEN
    try:
        # Cast to int to prevent string vs int comparison errors
        current_user_id = int(user["user_id"])
    except (KeyError, ValueError, TypeError) as e:
        print(f"Token Payload Error: {user} | Error: {e}")
        raise HTTPException(status_code=400, detail="Invalid User ID format in token")
        
    requested_product_id = int(order.product_id)

    # 2. VALIDATE USER (Call User Service)
    user_res = call_service(f"{USER_SERVICE}/users", authorization)
    if user_res.status_code != 200:
        print(f"User Service Error: {user_res.status_code} - {user_res.text}")
        raise HTTPException(status_code=400, detail="User Service validation failed")
    
    try:
        all_users = user_res.json()
        # Verify user exists in profile database with strict int casting
        user_exists = any(int(u["id"]) == current_user_id for u in all_users)
        
        if not user_exists:
            # Enhanced debug logging for troubleshooting
            print(f"CRITICAL: User ID {current_user_id} not found in list: {all_users}")
            raise HTTPException(status_code=400, detail="User not found in profile database")
    except (ValueError, TypeError, KeyError) as e:
        print(f"Parsing error for User Service response: {e}")
        raise HTTPException(status_code=500, detail="Failed to parse User Service data")

    # 3. VALIDATE PRODUCT (Call Product Service)
    prod_res = call_service(f"{PRODUCT_SERVICE}/products", authorization)
    if prod_res.status_code != 200:
        print(f"Product Service Error: {prod_res.status_code} - {prod_res.text}")
        raise HTTPException(status_code=400, detail="Product Service validation failed")
    
    try:
        all_prods = prod_res.json()
        # Verify product exists in inventory with strict int casting
        product_exists = any(int(p["id"]) == requested_product_id for p in all_prods)
        
        if not product_exists:
            print(f"CRITICAL: Product ID {requested_product_id} not found in list: {all_prods}")
            raise HTTPException(status_code=400, detail="Product not found")
    except (ValueError, TypeError, KeyError) as e:
        print(f"Parsing error for Product Service response: {e}")
        raise HTTPException(status_code=500, detail="Failed to parse Product Service data")

    # 4. SAVE ORDER TO DB
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO orders (user_id, product_id) VALUES (%s, %s) RETURNING id",
            (current_user_id, requested_product_id)
        )
        order_id = cur.fetchone()[0]
        conn.commit()
        print(f"✅ Created Order #{order_id} for User {current_user_id}")
        return {"order_id": order_id, "user_id": current_user_id, "product_id": requested_product_id}
    except Exception as e:
        conn.rollback()
        print(f"Order DB Insert Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to write order to database")
    finally:
        cur.close()
        conn.close()

@app.get("/orders")
def get_orders(user=Depends(verify_token)):
    conn = get_connection()
    cur = conn.cursor()
    try:
        current_user_id = int(user["user_id"])
        # Professional standard: Filter orders by user_id for security
        cur.execute("SELECT id, user_id, product_id FROM orders WHERE user_id = %s", (current_user_id,))
        rows = cur.fetchall()
        return [{"id": r[0], "user_id": r[1], "product_id": r[2]} for r in rows]
    except Exception as e:
        print(f"Fetch Orders Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch orders")
    finally:
        cur.close()
        conn.close()